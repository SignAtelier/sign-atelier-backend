import asyncio
import io
from collections.abc import Iterator
from datetime import datetime, timedelta

from starlette.config import Config

from app.config.constants import CODE, MESSAGE, S3
from app.exception.custom_exception import AppException
from app.utils.exception import raise_save_failed


config = Config(".env")


class GCSObjectStorage:
    def __init__(self):
        from google.cloud import storage

        self.client = storage.Client()
        self.bucket = self.client.bucket(config("GCS_BUCKET"))

    async def upload(self, buffer: io.BytesIO, file_name: str) -> None:
        await asyncio.to_thread(self._upload, buffer, file_name)

    async def generate_read_url(self, file_name: str) -> str:
        return await asyncio.to_thread(self._generate_read_url, file_name)

    async def delete(self, file_name: str) -> None:
        await asyncio.to_thread(self._delete, file_name)

    async def copy_and_delete(self, source: str, destination: str) -> None:
        await asyncio.to_thread(self._copy_and_delete, source, destination)

    async def get_stream(self, file_name: str) -> tuple[Iterator[bytes], str]:
        try:
            blob = self.bucket.blob(file_name)
            content_type = blob.content_type or "image/png"
            content = await asyncio.to_thread(blob.download_as_bytes)
        except Exception as exc:
            raise AppException(
                status=404,
                code=CODE.ERROR.NOT_FOUND,
                message=MESSAGE.ERROR.NOT_FOUND,
            ) from exc

        return iter([content]), content_type

    async def list_keys(
        self, prefix: str
    ) -> list[tuple[str, datetime | None]]:
        return await asyncio.to_thread(self._list_keys, prefix)

    def _upload(self, buffer: io.BytesIO, file_name: str) -> None:
        try:
            buffer.seek(0)
            blob = self.bucket.blob(file_name)
            blob.upload_from_file(buffer, content_type="image/png")
        except Exception as exc:
            raise_save_failed(exc)

    def _generate_read_url(self, file_name: str) -> str:
        try:
            blob = self.bucket.blob(file_name)

            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=S3.PresignedUrl),
                method="GET",
            )
        except Exception as exc:
            raise AppException(
                status=500,
                code=CODE.ERROR.PRESIGNED_URL_FAILED,
                message=MESSAGE.ERROR.PRESIGNED_URL_FAILED,
            ) from exc

    def _delete(self, file_name: str) -> None:
        blob = self.bucket.blob(file_name)
        blob.delete()

    def _copy_and_delete(self, source: str, destination: str) -> None:
        try:
            source_blob = self.bucket.blob(source)

            self.bucket.copy_blob(source_blob, self.bucket, destination)
            source_blob.delete()
        except Exception as exc:
            raise_save_failed(exc)

    def _list_keys(self, prefix: str) -> list[tuple[str, datetime | None]]:
        return [
            (blob.name, blob.updated)
            for blob in self.client.list_blobs(self.bucket, prefix=prefix)
        ]
