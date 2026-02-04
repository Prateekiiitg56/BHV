from abc import ABC, abstractmethod
from typing import Optional, List, Dict


class StorageAdapter(ABC):
    @abstractmethod
    def save(self, relative_path: str, data: bytes, user_id: str, action: str, message: Optional[str] = None) -> str:
        """Save bytes into storage and return a version id / commit hash."""

    @abstractmethod
    def get(self, relative_path: str, version: Optional[str] = None) -> bytes:
        """Retrieve file bytes. If version is None, return latest."""

    @abstractmethod
    def history(self, relative_path: str) -> List[Dict]:
        """Return chronological list of versions/commits for the given path."""
