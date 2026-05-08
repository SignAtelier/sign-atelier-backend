import asyncio
import io
from collections.abc import Iterator
from datetime import datetime

import boto3
from starlette.config import Config

from app.config.constants import CODE, MESSAGE, S3
from app.config.s3 import s3_client
from app.exception.custom_exception import AppException
from app.utils.exception import raise_save_failed


config = Config(".env")


class S3ObjectStorage:
    def __init__(self):
        self.bucket = config("S3_BUCKET")

    async def upload(self, buffer: io.BytesIO, file_name: str) -> None:
        await asyncio.to_thread(self._upload, buffer, file_name)

    async def generate_read_url(self, file_name: str) -> str:
        return await asyncio.to_thread(self._generate_read_url, file_name)

    async def delete(self, file_name: str) -> None:
        await asyncio.to_thread(
            s3_client.delete_object,
            Bucket=self.bucket,
            Key=file_name,
        )

    async def copy_and_delete(self, source: str, destination: str) -> None:
        await asyncio.to_thread(self._copy_and_delete, source, destination)

    async def get_stream(self, file_name: str) -> tuple[Iterator[bytes], str]:
        try:
            response = await asyncio.to_thread(
                s3_client.get_object,
                Bucket=self.bucket,
                Key=file_name,
            )
        except Exception as exc:
            raise AppException(
                status=404,
                code=CODE.ERROR.NOT_FOUND,
                message=MESSAGE.ERROR.NOT_FOUND,
            ) from exc

        return response["Body"].iter_chunks(), response.get(
            "ContentType", "image/png"
        )

    async def list_keys(
        self, prefix: str
    ) -> list[tuple[str, datetime | None]]:
        return await asyncio.to_thread(self._list_keys, prefix)

    def _upload(self, buffer: io.BytesIO, file_name: str) -> None:
        try:
            buffer.seek(0)
            s3_client.upload_fileobj(buffer, self.bucket, file_name)
        except Exception as exc:
            raise_save_failed(exc)

    def _generate_read_url(self, file_name: str) -> str:
        try:
            return s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": file_name},
                ExpiresIn=S3.PresignedUrl,
            )
        except Exception as exc:
            raise AppException(
                status=500,
                code=CODE.ERROR.PRESIGNED_URL_FAILED,
                message=MESSAGE.ERROR.PRESIGNED_URL_FAILED,
            ) from exc

    def _copy_and_delete(self, source: str, destination: str) -> None:
        try:
            resource_s3 = boto3.resource(
                S3.ResourceName,
                aws_access_key_id=config("CREDENTIALS_ACCESS_KEY"),
                aws_secret_access_key=config("CREDENTIALS_SECRET_KEY"),
            )
            copy_source = {"Bucket": self.bucket, "Key": source}

            resource_s3.meta.client.copy(copy_source, self.bucket, destination)
            s3_client.delete_object(Bucket=self.bucket, Key=source)
        except Exception as exc:
            raise_save_failed(exc)

    def _list_keys(self, prefix: str) -> list[tuple[str, datetime | None]]:
        paginator = s3_client.get_paginator("list_objects_v2")
        objects = []

        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for item in page.get("Contents", []):
                key = item.get("Key")

                if key:
                    objects.append((key, item.get("LastModified")))

        return objects
