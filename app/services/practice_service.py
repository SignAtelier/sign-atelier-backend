from starlette.config import Config

from app.config.s3 import s3_client
from app.db.crud.practice import (
    delete_practices,
    get_practices_by_sign_id,
    save_practice,
)


config = Config(".env")


async def save_practice_db(file_name, sign_id):
    return await save_practice(file_name, sign_id)


async def get_practices_db(sign_id):
    return await get_practices_by_sign_id(sign_id)


async def delete_practices_s3(file_names):
    for file_name in file_names:
        s3_client.delete_object(Bucket=config("S3_BUCKET"), Key=file_name)


async def delete_practices_db(file_names):
    return await delete_practices(file_names)
