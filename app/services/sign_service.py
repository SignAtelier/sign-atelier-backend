import io

import boto3
from PIL import Image
from starlette.config import Config

from app.config.constants import CODE, MESSAGE, S3
from app.config.s3 import s3_client
from app.db.crud.sign import save_sign
from app.exception.custom_exception import AppException

config = Config(".env")


def generate_sign_ai():
    img = Image.new("RGB", (512, 256), color="black")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def upload_temp_sign(buffer: io.BytesIO, bucket: str, file_name: str) -> str:
    buffer.seek(0)

    s3_client.upload_fileobj(buffer, bucket, file_name)

    return generate_presigned_url(file_name)


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


def move_file_s3(
    temp_file_name: str, bucket: str, final_file_name: str
) -> bool:
    try:
        resource_s3 = boto3.resource(
            S3.ResourceName,
            aws_access_key_id=config("CREDENTIALS_ACCESS_KEY"),
            aws_secret_access_key=config("CREDENTIALS_SECRET_KEY"),
        )
        copy_source = {"Bucket": bucket, "Key": temp_file_name}

        resource_s3.meta.client.copy(copy_source, bucket, final_file_name)
        s3_client.delete_object(Bucket=bucket, Key=temp_file_name)
    except Exception as exc:
        raise AppException(
            status=500,
            code=CODE.ERROR.SAVE_FAILED,
            message=MESSAGE.ERROR.SAVE_FAILED,
        ) from exc


async def save_sign_db(user, file_name):
    await save_sign(user, file_name)
