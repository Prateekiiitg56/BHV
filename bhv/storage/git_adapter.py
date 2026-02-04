import os
import threading
from typing import Optional, List, Dict
from git import Repo, Actor

from .base import StorageAdapter


class GitAdapter(StorageAdapter):
    """A simple Git-backed storage adapter.

    This adapter stores each patient's vault under a separate directory
    (root_dir/<patient_id>/...). Each save writes the file and creates
    a git commit with metadata in the message.
    """

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)
        self._repos = {}  # cache patient_id -> Repo
        self._locks = {}  # patient_id -> threading.Lock

    def _ensure_repo(self, patient_id: str) -> Repo:
        repo_path = os.path.join(self.root_dir, patient_id)
        if patient_id not in self._repos:
            os.makedirs(repo_path, exist_ok=True)
            if not os.path.exists(os.path.join(repo_path, '.git')):
                repo = Repo.init(repo_path)
            else:
                repo = Repo(repo_path)
            self._repos[patient_id] = repo
            self._locks[patient_id] = threading.Lock()
        return self._repos[patient_id]

    def save(self, relative_path: str, data: bytes, user_id: str, action: str, message: Optional[str] = None) -> str:
        # relative_path expected: '<patient_id>/path/to/file.ext'
        parts = relative_path.split(os.sep)
        if len(parts) < 2:
            raise ValueError("relative_path must start with '<patient_id>/...'")
        patient_id = parts[0]
        repo = self._ensure_repo(patient_id)
        lock = self._locks[patient_id]
        full_path = os.path.join(repo.working_tree_dir, *parts[1:])
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with lock:
            with open(full_path, 'wb') as f:
                f.write(data)

            repo.index.add([os.path.relpath(full_path, repo.working_tree_dir)])
            actor = Actor("BHV System", "no-reply@example.com")
            commit_message = message or f"{action} by user {user_id} on {relative_path}"
            commit = repo.index.commit(commit_message, author=actor, committer=actor)
            return commit.hexsha

    def get(self, relative_path: str, version: Optional[str] = None) -> bytes:
        parts = relative_path.split(os.sep)
        if len(parts) < 2:
            raise ValueError("relative_path must start with '<patient_id>/...'")
        patient_id = parts[0]
        repo = self._ensure_repo(patient_id)
        rel_path = os.path.join(*parts[1:])
        if version is None:
            # read from working tree
            target = os.path.join(repo.working_tree_dir, rel_path)
            with open(target, 'rb') as f:
                return f.read()
        else:
            commit = repo.commit(version)
            blob = commit.tree / rel_path
            return blob.data_stream.read()

    def history(self, relative_path: str) -> List[Dict]:
        parts = relative_path.split(os.sep)
        if len(parts) < 2:
            raise ValueError("relative_path must start with '<patient_id>/...'")
        patient_id = parts[0]
        repo = self._ensure_repo(patient_id)
        rel_path = os.path.join(*parts[1:])
        commits = list(repo.iter_commits(paths=rel_path))
        # chronological (oldest first)
        commits.reverse()
        result = []
        for c in commits:
            result.append({
                'hexsha': c.hexsha,
                'author': str(c.author),
                'message': c.message.strip(),
                'datetime': c.committed_datetime.isoformat(),
            })
        return result
