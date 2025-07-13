from starlette.config import Config

from app.db.crud.practice import get_practices_by_sign_id
from app.db.crud.sign import hard_delete_sign
from app.services.practice_service import (
    delete_practices_db,
    delete_practices_s3,
)
from app.utils.s3 import delete_s3_file


config = Config(".env")


async def hard_delete_process(sign):
    practices = await get_practices_by_sign_id(sign.id)
    file_names = [practice.file_name for practice in practices]

    await hard_delete_sign(sign)
    await delete_practices_db(file_names)
    delete_s3_file(config("S3_BUCKET"), sign.outline_file_name)
    delete_s3_file(config("S3_BUCKET"), sign.file_name)
    await delete_practices_s3(file_names)
