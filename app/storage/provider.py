import os

from app.storage.base import ObjectStorage


_storage: ObjectStorage | None = None


def get_storage() -> ObjectStorage:
    global _storage

    if _storage is None:
        storage_provider = os.getenv("STORAGE_PROVIDER", "s3").lower()

        if storage_provider == "s3":
            from app.storage.s3_storage import S3ObjectStorage

            _storage = S3ObjectStorage()
        elif storage_provider == "gcs":
            from app.storage.gcs_storage import GCSObjectStorage

            _storage = GCSObjectStorage()
        else:
            raise ValueError(f"Unsupported storage provider: {storage_provider}")

    return _storage
