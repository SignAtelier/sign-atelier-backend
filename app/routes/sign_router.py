import uuid

from fastapi import APIRouter, Depends, Form
from starlette.config import Config

from app.config.constants import CODE, MESSAGE
from app.depends.auth_deps import get_current_user
from app.services.sign_service import (
    edit_name,
    generate_presigned_url,
    generate_sign_ai,
    get_signs_list,
    move_file_s3,
    save_sign_db,
    upload_temp_sign,
)

router = APIRouter()
config = Config(".env")


@router.post("/request")
async def generate_sign(
    user=Depends(get_current_user),
):
    sign_buffer = generate_sign_ai()
    social_id = user["social_id"]
    provider = user["provider"]
    user_info = social_id + provider

    file_name = f"temp/{user_info}/{uuid.uuid4().hex}.png"

    url = upload_temp_sign(
        buffer=sign_buffer, bucket=config("S3_BUCKET"), file_name=file_name
    )

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
    final_file_name = temp_file_name.replace("temp/", "signs/", 1)

    move_file_s3(temp_file_name, config("S3_BUCKET"), final_file_name)
    await save_sign_db(user, final_file_name)

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
