from .local_storage import LocalStorage
from .s3_storage import S3Storage

def get_storage(storage_type: str, **kwargs):
    """
    Factory method to get the appropriate storage instance.

    :param storage_type: The type of storage ('local' or 's3').
    :param kwargs: Additional arguments such as 'base_path', 'subdirectory', or S3-specific keys.
    :return: An instance of the storage class (LocalStorage or S3Storage).
    """
    subdirectory = kwargs.get('subdirectory', None)

    if storage_type == 'local':
        return LocalStorage(
            base_path=kwargs.get('base_path', './data'),
            subdirectory=subdirectory
        )
    elif storage_type == 's3':
        return S3Storage(
            bucket_name=kwargs['bucket_name'],
            aws_access_key_id=kwargs['aws_access_key_id'],
            aws_secret_access_key=kwargs['aws_secret_access_key'],
            # subdirectory=subdirectory  # Optional if you implement it for S3
        )
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")
