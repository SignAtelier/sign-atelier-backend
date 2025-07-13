import io
import uuid

import requests
from fastapi import APIRouter, Body, Depends, File, Form, UploadFile
from starlette.config import Config

from app.config.constants import CODE, MESSAGE
from app.depends.auth_deps import get_current_user
from app.exception.custom_exception import AppException
from app.services.sign_service import (
    delete_sign_db,
    delete_sign_s3,
    edit_name,
    extract_outline,
    generate_sign_ai,
    get_sign_one,
    get_signs_list,
    hard_delete_sign_db,
    move_file_s3,
    restore_sign_db,
    save_sign_db,
)
from app.utils.s3 import generate_presigned_url, upload_sign


router = APIRouter()
config = Config(".env")


@router.post("/request")
async def generate_sign(
    name: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    image_bytes = await file.read()
    sign_buffer = generate_sign_ai(name, image_bytes)
    social_id = user["social_id"]
    provider = user["provider"]
    user_info = social_id + provider

    file_name = f"temp/{user_info}/{uuid.uuid4().hex}.png"

    upload_sign(
        buffer=sign_buffer, bucket=config("S3_BUCKET"), file_name=file_name
    )
    url = generate_presigned_url(file_name)

    return {
        "status": 201,
        "code": CODE.SUCCESS.SIGN_GENERATION_SUCCESS,
        "message": MESSAGE.SUCCESS.SIGN_GENERATION_SUCCESS,
        "detail": url,
    }


@router.post("/upload")
async def finalize_sign_upload(
    temp_file_name: str = Form(), user=Depends(get_current_user)
):
    final_file_name = temp_file_name.replace("temp", "signs", 1)

    move_file_s3(temp_file_name, config("S3_BUCKET"), final_file_name)

    sign_url = generate_presigned_url(final_file_name)
    response = requests.get(sign_url)
    buffer = io.BytesIO(response.content)
    outline_buffer = extract_outline(buffer)
    outline_file_name = final_file_name.replace("signs", "outline", 1)

    upload_sign(outline_buffer, config("S3_BUCKET"), outline_file_name)
    await save_sign_db(user, final_file_name, outline_file_name)

    return {
        "status": 201,
        "code": CODE.SUCCESS.SAVE_SUCCESS,
        "message": MESSAGE.SUCCESS.SAVE_SUCCESS,
    }


@router.get("/list")
async def get_signs(user=Depends(get_current_user)):
    signs = await get_signs_list(user)
    response = []

    for sign in signs:
        response.append(
            {
                "id": str(sign.id),
                "name": sign.name,
                "fileName": sign.file_name,
                "url": generate_presigned_url(sign.file_name),
                "createdAt": sign.created_at,
                "updatedAt": sign.updated_at,
                "isDeleted": sign.is_deleted,
                "deletedAt": sign.deleted_at,
            }
        )

    return {"status": 200, "signs": response}


@router.patch("/name")
async def edit_sign_name(
    sign_id: str = Form(),
    new_name: str = Form(),
    user=Depends(get_current_user),
):
    edited_sign = await edit_name(user, sign_id, new_name)
    response = {
        "id": str(edited_sign.id),
        "name": edited_sign.name,
        "udpatedAt": edited_sign.updated_at,
    }

    return {"status": 200, "editedSign": response}


@router.delete("/soft")
async def delete_sign(
    sign_id: str = Body(..., embed=True),
    user=Depends(get_current_user),
):
    deleted_sign = await delete_sign_db(user, sign_id)
    response = {
        "id": str(deleted_sign.id),
        "createdAt": deleted_sign.created_at,
        "deletedAt": deleted_sign.deleted_at,
        "fileName": deleted_sign.file_name,
        "isDeleted": deleted_sign.is_deleted,
        "name": deleted_sign.name,
        "updatedAt": deleted_sign.updated_at,
    }

    return {"status": 200, "deletedSign": response}


@router.post("/restore")
async def restore_sign(
    sign_id: str = Body(..., embed=True),
    user=Depends(get_current_user),
):
    restored_sign = await restore_sign_db(user, sign_id)
    response = {
        "id": str(restored_sign.id),
        "createdAt": restored_sign.created_at,
        "deletedAt": restored_sign.deleted_at,
        "fileName": restored_sign.file_name,
        "isDeleted": restored_sign.is_deleted,
        "name": restored_sign.name,
        "updatedAt": restored_sign.updated_at,
    }

    return {"status": 200, "restoredSign": response}


@router.delete("/hard")
async def hard_delete_sign(
    sign_id: str = Body(..., embed=True),
    _=Depends(get_current_user),
):
    file_name = await hard_delete_sign_db(sign_id)

    await delete_sign_s3(file_name)

    return {
        "status": 200,
        "code": CODE.SUCCESS.HARD_DELETE,
        "message": MESSAGE.SUCCESS.HARD_DELETE,
    }


@router.get("/sign/{sign_id}")
async def get_sign(sign_id: str, user=Depends(get_current_user)):
    sign = await get_sign_one(sign_id)

    if (
        sign.user.social_id != user["social_id"]
        and sign.user.provider != user["provider"]
    ):
        raise AppException(
            status=403,
            code=CODE.ERROR.FORBIDDEN,
            message=MESSAGE.ERROR.FORBIDDEN,
        )

    url = generate_presigned_url(sign.file_name)

    return {"status": 200, "url": url}


@router.get("/outline/{sign_id}")
async def get_sing_outline(sign_id: str, user=Depends(get_current_user)):
    sign = await get_sign_one(sign_id)

    if (
        sign.user.social_id != user["social_id"]
        and sign.user.provider != user["provider"]
    ):
        raise AppException(
            status=403,
            code=CODE.ERROR.FORBIDDEN,
            message=MESSAGE.ERROR.FORBIDDEN,
        )

    url = generate_presigned_url(sign.outline_file_name)

    return {"status": 200, "url": url}
