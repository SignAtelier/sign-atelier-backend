from datetime import datetime, timedelta, timezone

from app.config.constants import TempStorage
from app.db.crud.practice import get_practices_by_sign_id
from app.db.crud.sign import hard_delete_sign
from app.services.practice_service import (
    delete_practices_db,
    delete_practices_s3,
)
from app.storage import get_storage


async def hard_delete_process(sign):
    practices = await get_practices_by_sign_id(sign.id)
    file_names = [practice.file_name for practice in practices]

    await hard_delete_sign(sign)
    await delete_practices_db(file_names)
    storage = get_storage()

    await storage.delete(sign.outline_file_name)
    await storage.delete(sign.file_name)
    await delete_practices_s3(file_names)


async def cleanup_expired_temp_files():
    storage = get_storage()
    now = datetime.now(timezone.utc)
    expires_before = now - timedelta(seconds=TempStorage.EXPIRE_SECONDS)
    temp_files = await storage.list_keys(TempStorage.PREFIX)

    for file_name, last_modified in temp_files:
        if not last_modified:
            continue

        if last_modified.tzinfo is None:
            last_modified = last_modified.replace(tzinfo=timezone.utc)

        if last_modified < expires_before:
            await storage.delete(file_name)
