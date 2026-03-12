"""
BHV GitHub Private Repository Storage Adapter
===============================================
Each patient's images are stored in a PRIVATE GitHub repository created under
the *patient's* GitHub account (via a Personal Access Token they provide, or
via an admin service token that acts on their behalf).

Repository structure:
    img/
        <filename>
    metadata.json          ← global index of all uploads

Admin is added as a collaborator so they can view/moderate content.

Environment variables required:
    GITHUB_ADMIN_TOKEN    — GitHub Personal Access Token for the admin/service account
                            (needs `repo` scope to create private repos)
    GITHUB_ADMIN_USERNAME — GitHub username of the admin/service account
    GITHUB_ORG            — (optional) if set, repos are created under this org instead of the admin account

Storage mode:
    STORAGE_MODE=github   — use this adapter
    STORAGE_MODE=local    — use GitAdapter (default)
"""

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

from .base import StorageAdapter

GITHUB_API = "https://api.github.com"


class GitHubAdapter(StorageAdapter):
    """GitHub-backed storage adapter. Creates one private repo per patient."""

    def __init__(self):
        self.admin_token = os.environ.get("GITHUB_ADMIN_TOKEN", "")
        self.admin_username = os.environ.get("GITHUB_ADMIN_USERNAME", "")
        self.org = os.environ.get("GITHUB_ORG", "")  # optional

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, body=None) -> Dict:
        url = GITHUB_API + path
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = {}
            try:
                error_body = json.loads(e.read())
            except Exception:
                pass
            raise RuntimeError(
                f"GitHub API {method} {path} → {e.code}: {error_body.get('message', str(e))}"
            ) from e

    def _repo_name(self, patient_id: str) -> str:
        """Derive a safe, unique repo name from patient email."""
        safe = patient_id.replace("@", "-at-").replace(".", "-").lower()
        return f"bhv-vault-{safe}"

    def _repo_exists(self, repo_name: str) -> bool:
        owner = self.org or self.admin_username
        try:
            self._request("GET", f"/repos/{owner}/{repo_name}")
            return True
        except RuntimeError:
            return False

    def _ensure_repo(self, patient_id: str) -> str:
        """Create the private repo if it doesn't exist. Returns the HTML URL."""
        repo_name = self._repo_name(patient_id)
        owner = self.org or self.admin_username

        if not self._repo_exists(repo_name):
            endpoint = f"/orgs/{self.org}/repos" if self.org else "/user/repos"
            repo = self._request("POST", endpoint, {
                "name": repo_name,
                "private": True,
                "description": f"BHV Behavioral Health Vault — private records for {patient_id}",
                "auto_init": True,   # creates an initial commit so the repo has a valid HEAD
            })
            # Add admin as collaborator if storing under org or different account
            try:
                self._request(
                    "PUT",
                    f"/repos/{owner}/{repo_name}/collaborators/{self.admin_username}",
                    {"permission": "admin"},
                )
            except Exception:
                pass  # non-fatal
            return repo.get("html_url", f"https://github.com/{owner}/{repo_name}")

        return f"https://github.com/{owner}/{repo_name}"

    def _get_file_sha(self, owner: str, repo_name: str, path: str) -> Optional[str]:
        """Get the blob SHA of an existing file (needed for updates via API)."""
        try:
            result = self._request("GET", f"/repos/{owner}/{repo_name}/contents/{path}")
            return result.get("sha")
        except RuntimeError:
            return None

    def _put_file(self, owner: str, repo_name: str, path: str, content_bytes: bytes, commit_msg: str):
        """Create or update a file in the GitHub repo."""
        sha = self._get_file_sha(owner, repo_name, path)
        encoded = base64.b64encode(content_bytes).decode()
        body = {
            "message": commit_msg,
            "content": encoded,
        }
        if sha:
            body["sha"] = sha
        return self._request("PUT", f"/repos/{owner}/{repo_name}/contents/{path}", body)

    def _get_metadata(self, owner: str, repo_name: str) -> Dict:
        """Download and parse the global metadata.json from the repo."""
        try:
            result = self._request("GET", f"/repos/{owner}/{repo_name}/contents/metadata.json")
            raw = base64.b64decode(result["content"]).decode()
            return json.loads(raw)
        except Exception:
            return {"entries": []}

    def _update_metadata(self, owner: str, repo_name: str, filename: str,
                         patient_id: str, narrative: str, extra: Dict):
        meta = self._get_metadata(owner, repo_name)
        meta.setdefault("entries", [])
        meta["entries"].append({
            "filename": filename,
            "path": f"img/{filename}",
            "patient_id": patient_id,
            "narrative": narrative,
            "timestamp": datetime.utcnow().isoformat(),
            **extra,
        })
        content = json.dumps(meta, indent=2).encode()
        self._put_file(owner, repo_name, "metadata.json", content,
                       f"Update metadata for {filename}")

    # ------------------------------------------------------------------
    # StorageAdapter interface
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """Return True only if the required env vars are present."""
        return bool(self.admin_token and self.admin_username)

    def save(self, relative_path: str, data: bytes, user_id: str, action: str,
             message: Optional[str] = None) -> str:
        """
        Push image to patient's GitHub repo.

        relative_path: '<patient_id>/<filename>'
        Returns the HTML URL of the repository.
        """
        parts = relative_path.replace("\\", "/").split("/")
        if len(parts) < 2:
            raise ValueError("relative_path must be '<patient_id>/<filename>'")
        patient_id = parts[0]
        filename = "/".join(parts[1:])

        owner = self.org or self.admin_username
        repo_name = self._repo_name(patient_id)

        # Ensure the private repo exists
        repo_url = self._ensure_repo(patient_id)

        # Push the image to img/<filename>
        commit_msg = message or f"{action} by {user_id}"
        self._put_file(owner, repo_name, f"img/{filename}", data, commit_msg)

        return repo_url

    def save_with_metadata(self, relative_path: str, data: bytes, user_id: str,
                           action: str, narrative: str, extra: Dict = None) -> str:
        """Save image AND update metadata.json in one operation."""
        repo_url = self.save(relative_path, data, user_id, action)

        parts = relative_path.replace("\\", "/").split("/")
        patient_id = parts[0]
        filename = "/".join(parts[1:])
        owner = self.org or self.admin_username
        repo_name = self._repo_name(patient_id)

        self._update_metadata(owner, repo_name, filename, patient_id, narrative, extra or {})
        return repo_url

    def get(self, relative_path: str, version: Optional[str] = None) -> bytes:
        parts = relative_path.replace("\\", "/").split("/")
        patient_id = parts[0]
        filename = "/".join(parts[1:])
        owner = self.org or self.admin_username
        repo_name = self._repo_name(patient_id)
        result = self._request("GET", f"/repos/{owner}/{repo_name}/contents/img/{filename}")
        return base64.b64decode(result["content"])

    def history(self, relative_path: str) -> List[Dict]:
        parts = relative_path.replace("\\", "/").split("/")
        patient_id = parts[0]
        filename = "/".join(parts[1:])
        owner = self.org or self.admin_username
        repo_name = self._repo_name(patient_id)
        try:
            commits = self._request("GET", f"/repos/{owner}/{repo_name}/commits?path=img/{filename}")
            return [
                {
                    "hexsha": c["sha"],
                    "author": c["commit"]["author"]["name"],
                    "message": c["commit"]["message"],
                    "datetime": c["commit"]["author"]["date"],
                }
                for c in commits
            ]
        except Exception:
            return []

    def head(self, relative_path: str) -> Optional[str]:
        hist = self.history(relative_path)
        return hist[0]["hexsha"] if hist else None

    def save_with_parent(self, relative_path: str, data: bytes, user_id: str,
                         action: str, parent=None, message=None) -> str:
        return self.save(relative_path, data, user_id, action, message)

    def repo_url_for_patient(self, patient_id: str) -> str:
        owner = self.org or self.admin_username
        return f"https://github.com/{owner}/{self._repo_name(patient_id)}"
