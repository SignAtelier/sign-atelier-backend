from bson import ObjectId

from app.config.constants import CODE, MESSAGE
from app.db.crud.sign import get_sign_by_id
from app.exception.custom_exception import AppException
from app.models.practice import PracticeRecord


async def save_practice(file_name: str, sign_id: str):
    sign = await get_sign_by_id(sign_id)

    if not sign:
        raise AppException(
            status=404,
            code=CODE.ERROR.NOT_FOUND,
            message=MESSAGE.ERROR.NOT_FOUND,
        )

    practice_record = PracticeRecord(
        file_name=file_name,
        sign=sign,
    )

    return await practice_record.insert()


async def get_practice(sign_id: str):
    return (
        await PracticeRecord.find(PracticeRecord.sign.id == ObjectId(sign_id))
        .sort("-created_at")
        .to_list()
    )
