from abc import ABC, abstractmethod
from typing import BinaryIO, List

class StorageInterface(ABC):
    @abstractmethod
    def save_file(self, file_data: BinaryIO, file_name: str) -> str:
        """Save a file and return its public URL or local path"""
        pass

    @abstractmethod
    def get_file_url(self, file_name: str) -> str:
        """Get the public URL or local path of a file"""
        pass

    @abstractmethod
    def delete_file(self, file_name: str) -> bool:
        """Delete a file and return True if successful"""
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        """List all files with an optional prefix"""
        pass