import io

from starlette.config import Config

from app.config.constants import CODE, MESSAGE, S3
from app.config.s3 import s3_client
from app.exception.custom_exception import AppException
from app.utils.exception import raise_save_failed


config = Config(".env")


def upload_sign(buffer: io.BytesIO, bucket: str, file_name: str) -> str:
    try:
        buffer.seek(0)

        s3_client.upload_fileobj(buffer, bucket, file_name)
    except Exception as exc:
        raise_save_failed(exc)


def generate_presigned_url(file_name: str):
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": config("S3_BUCKET"), "Key": file_name},
            ExpiresIn=S3.PresignedUrl,
        )

        return response
    except Exception as exc:
        raise AppException(
            status=500,
            code=CODE.ERROR.PRESIGNED_URL_FAILED,
            message=MESSAGE.ERROR.PRESIGNED_URL_FAILED,
        ) from exc
