import io

from app.config.s3 import s3_client


def upload_sign(buffer: io.BytesIO, bucket: str, file_name: str) -> str:
    buffer.seek(0)

    s3_client.upload_fileobj(buffer, bucket, file_name)
