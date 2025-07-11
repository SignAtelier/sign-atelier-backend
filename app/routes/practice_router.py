import io
import uuid

from fastapi import APIRouter, Depends, Form, UploadFile
from starlette.config import Config

from app.config.constants import CODE, MESSAGE
from app.depends.auth_deps import get_current_user
from app.exception.custom_exception import AppException
from app.services.practice_service import save_practice_db
from app.utils.s3.upload import upload_sign

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

        upload_sign(
            buffer=buffer, bucket=config("S3_BUCKET"), file_name=file_name
        )
        await save_practice_db(user, file_name, sign_id)

        return {
            "status": 201,
            "code": CODE.SUCCESS.PRCTICE_SAVED,
            "message": MESSAGE.SUCCESS.PRCTICE_SAVED,
            "detail": file_name,
        }
    except Exception as exc:
        raise AppException(
            status=500,
            code=CODE.ERROR.PRCTICE_FAILED,
            message=MESSAGE.ERROR.PRCTICE_FAILED,
        ) from exc
