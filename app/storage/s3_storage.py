from typing import BinaryIO, List
from .storage_interface import StorageInterface
import boto3

class S3Storage(StorageInterface):
    def __init__(self, bucket_name: str, aws_access_key_id: str, aws_secret_access_key: str):
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3',
                               aws_access_key_id=aws_access_key_id,
                               aws_secret_access_key=aws_secret_access_key)

    def save_file(self, file_data: BinaryIO, file_name: str) -> str:
        # Implement S3 upload logic here
        pass

    def get_file_url(self, file_name: str) -> str:
        # Implement S3 URL generation logic here
        pass

    def delete_file(self, file_name: str) -> bool:
        # Implement S3 delete logic here
        pass

    def list_files(self, prefix: str = "") -> List[str]:
        # Implement S3 list objects logic here
        pass