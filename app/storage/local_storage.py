import os
from typing import BinaryIO, List
from .storage_interface import StorageInterface


class LocalStorage:

    def __init__(self, subdirectory=None, base_path='./data', **kwargs):
        self.base_path = base_path
        self.subdirectory = subdirectory

        # Ensure the base directory exists
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        # Set up the subdirectory for this blueprint
        if self.subdirectory:
            self.base_path = os.path.join(self.base_path, self.subdirectory)
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)

    def save_file(self, file, filename, subfolder=None):
        # Create a subfolder (like job_report_id) if needed
        file_path = os.path.join(self.base_path, subfolder, filename) if subfolder else os.path.join(self.base_path,
                                                                                                     filename)

        # Ensure subfolder exists
        if subfolder and not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        # Save the file in binary mode
        with open(file_path, 'wb') as f:
            f.write(file.read())

        return file_path

    def get_file_url(self, file_name: str, subfolder: str = None) -> str:
        """
        Get the full path to the file, including subfolder (e.g., job_report_id).
        """
        return os.path.join(self.base_path, subfolder, file_name) if subfolder else os.path.join(self.base_path,
                                                                                                 file_name)

    def delete_file(self, file_name: str, subfolder: str = None) -> bool:
        """
        Delete a file, including subfolder (e.g., job_report_id) if provided.
        """
        file_path = os.path.join(self.base_path, subfolder, file_name) if subfolder else os.path.join(self.base_path,
                                                                                                      file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def list_files(self, prefix: str = "", subfolder: str = None) -> List[str]:
        """
        List files in the directory, optionally within a subfolder and filtered by a prefix.
        """
        directory = os.path.join(self.base_path, subfolder) if subfolder else self.base_path
        if not os.path.exists(directory):
            return []

        files = os.listdir(directory)
        return [f for f in files if f.startswith(prefix)]