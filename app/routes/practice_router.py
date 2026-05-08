import io
import uuid
from typing import List

from fastapi import APIRouter, Body, Depends, Form, UploadFile
from starlette.responses import StreamingResponse

from app.config.constants import CODE, MESSAGE
from app.depends.auth_deps import get_current_user
from app.exception.custom_exception import AppException
from app.services.practice_service import (
    delete_practices_db,
    delete_practices_s3,
    get_practices_db,
    save_practice_db,
)
from app.storage import get_storage


router = APIRouter()


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
        await get_storage().upload(buffer, file_name)
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


@router.get("/download")
async def download_practice(file_name: str, user=Depends(get_current_user)):
    social_id = user["social_id"]
    provider = user["provider"]
    user_prefix = f"practices/{social_id}{provider}/"

    if not file_name.startswith(user_prefix):
        raise AppException(
            status=403,
            code=CODE.ERROR.FORBIDDEN,
            message=MESSAGE.ERROR.FORBIDDEN,
        )

    try:
        stream, content_type = await get_storage().get_stream(file_name)
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status=404,
            code=CODE.ERROR.NOT_FOUND,
            message=MESSAGE.ERROR.NOT_FOUND,
        ) from exc

    return StreamingResponse(
        stream,
        media_type=content_type,
        headers={
            "Content-Disposition": 'attachment; filename="practice.png"'
        },
    )


@router.delete("")
async def delete_practices(
    file_names: List[str] = Body(...), _=Depends(get_current_user)
):
    deleted_count = await delete_practices_db(file_names)

    if not len(file_names) == deleted_count:
        raise AppException(
            status=500,
            code=CODE.ERROR.DELETE_FAILED_DB,
            message=MESSAGE.ERROR.DELETE_FAILED_DB,
        )

    await delete_practices_s3(file_names)

    return {
        "code": CODE.SUCCESS.DELETE_SUCCESS,
        "message": MESSAGE.SUCCESS.DELETE_SUCCESS,
    }
