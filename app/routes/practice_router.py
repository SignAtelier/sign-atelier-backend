import io
import uuid

from fastapi import APIRouter, Depends, Form, UploadFile
from starlette.config import Config

from app.config.constants import CODE, MESSAGE
from app.depends.auth_deps import get_current_user
from app.exception.custom_exception import AppException
from app.services.practice_service import get_practices_db, save_practice_db
from app.utils.s3 import upload_sign


router = APIRouter()
config = Config(".env")


@router.post("/upload")
async def upload_practice(
    file: UploadFile | None = None,
    sign_id: str = Form(),
    user=Depends(get_current_user),
):
    try:
        if not file or not sign_id:
            raise AppException(
                status=400,
                code=CODE.ERROR.MISSING_FIELD,
                message=MESSAGE.ERROR.MISSING_FIELD,
            )

        social_id = user["social_id"]
        provider = user["provider"]
        user_info = social_id + provider
        file_name = f"practices/{user_info}/{sign_id}/{uuid.uuid4().hex}.png"

        buffer = io.BytesIO(await file.read())

        practice = await save_practice_db(file_name, sign_id)
        upload_sign(
            buffer=buffer, bucket=config("S3_BUCKET"), file_name=file_name
        )
        response = {
            "id": practice.id,
            "fileName": practice.file_name,
            "createdAt": practice.created_at,
            "updatedAt": practice.updated_at,
        }

        return {
            "status": 201,
            "code": CODE.SUCCESS.PRCTICE_SAVED,
            "message": MESSAGE.SUCCESS.PRCTICE_SAVED,
            "detail": response,
        }
    except Exception as exc:
        print(exc)
        raise AppException(
            status=500,
            code=CODE.ERROR.PRCTICE_FAILED,
            message=MESSAGE.ERROR.PRCTICE_FAILED,
        ) from exc


@router.get("/list")
async def get_practices(sign_id: str, _=Depends(get_current_user)):
    practices_db = await get_practices_db(sign_id)

    if len(practices_db) == 0:
        return []

    response = []

    for practice in practices_db:
        item = {
            "id": str(practice.id),
            "fileName": practice.file_name,
            "createdAt": practice.created_at,
            "updatedAt": practice.updated_at,
        }

        response.append(item)

    return response
