from app.db.crud.practice import (
    delete_practices,
    get_practices_by_sign_id,
    save_practice,
)
from app.storage import get_storage


async def save_practice_db(file_name, sign_id):
    return await save_practice(file_name, sign_id)


async def get_practices_db(sign_id):
    return await get_practices_by_sign_id(sign_id)


async def delete_practices_s3(file_names):
    storage = get_storage()

    for file_name in file_names:
        await storage.delete(file_name)


async def delete_practices_db(file_names):
    return await delete_practices(file_names)
