import uuid

from fastapi import APIRouter, Depends
from starlette.config import Config

from app.config.constants import CODE, MESSAGE
from app.depends.auth_deps import get_current_user
from app.services.sign_service import generate_sign_ai, upload_temp_sign

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
