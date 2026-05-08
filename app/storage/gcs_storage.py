import asyncio
import io
import logging
from collections.abc import Iterator
from datetime import datetime, timedelta
from time import perf_counter

from starlette.config import Config

from app.config.constants import CODE, MESSAGE, S3
from app.exception.custom_exception import AppException
from app.utils.exception import raise_save_failed


config = Config(".env")
logger = logging.getLogger(__name__)


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
        started_at = perf_counter()
        try:
            buffer.seek(0)
            blob = self.bucket.blob(file_name)
            logger.info(
                "gcs.upload.start bucket=%s file=%s bytes=%s",
                self.bucket.name,
                file_name,
                buffer.getbuffer().nbytes,
            )
            blob.upload_from_file(buffer, content_type="image/png")
            logger.info(
                "gcs.upload.done bucket=%s file=%s elapsed=%.2fs",
                self.bucket.name,
                file_name,
                perf_counter() - started_at,
            )
        except Exception as exc:
            logger.exception(
                "gcs.upload.failed bucket=%s file=%s elapsed=%.2fs",
                self.bucket.name,
                file_name,
                perf_counter() - started_at,
            )
            raise_save_failed(exc)

    def _generate_read_url(self, file_name: str) -> str:
        started_at = perf_counter()
        try:
            blob = self.bucket.blob(file_name)
            logger.info(
                "gcs.read_url.start bucket=%s file=%s",
                self.bucket.name,
                file_name,
            )

            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=S3.PresignedUrl),
                method="GET",
            )
            logger.info(
                "gcs.read_url.done bucket=%s file=%s elapsed=%.2fs",
                self.bucket.name,
                file_name,
                perf_counter() - started_at,
            )
            return url
        except Exception as exc:
            logger.exception(
                "gcs.read_url.failed bucket=%s file=%s elapsed=%.2fs",
                self.bucket.name,
                file_name,
                perf_counter() - started_at,
            )
            raise AppException(
                status=500,
                code=CODE.ERROR.PRESIGNED_URL_FAILED,
                message=MESSAGE.ERROR.PRESIGNED_URL_FAILED,
            ) from exc

    def _delete(self, file_name: str) -> None:
        started_at = perf_counter()
        blob = self.bucket.blob(file_name)
        logger.info("gcs.delete.start bucket=%s file=%s", self.bucket.name, file_name)
        blob.delete()
        logger.info(
            "gcs.delete.done bucket=%s file=%s elapsed=%.2fs",
            self.bucket.name,
            file_name,
            perf_counter() - started_at,
        )

    def _copy_and_delete(self, source: str, destination: str) -> None:
        started_at = perf_counter()
        try:
            source_blob = self.bucket.blob(source)
            logger.info(
                "gcs.copy_delete.start bucket=%s source=%s destination=%s",
                self.bucket.name,
                source,
                destination,
            )

            self.bucket.copy_blob(source_blob, self.bucket, destination)
            source_blob.delete()
            logger.info(
                "gcs.copy_delete.done bucket=%s source=%s destination=%s elapsed=%.2fs",
                self.bucket.name,
                source,
                destination,
                perf_counter() - started_at,
            )
        except Exception as exc:
            logger.exception(
                "gcs.copy_delete.failed bucket=%s source=%s destination=%s elapsed=%.2fs",
                self.bucket.name,
                source,
                destination,
                perf_counter() - started_at,
            )
            raise_save_failed(exc)

    def _list_keys(self, prefix: str) -> list[tuple[str, datetime | None]]:
        return [
            (blob.name, blob.updated)
            for blob in self.client.list_blobs(self.bucket, prefix=prefix)
        ]
