import base64
import io
import logging
from datetime import datetime, timedelta, timezone
from time import perf_counter
import uuid

import boto3
import cv2
import numpy as np
import requests
from PIL import Image
from skimage.morphology import skeletonize
from starlette.config import Config

from app.ai.providers import get_sign_provider
from app.config.constants import CODE, MESSAGE, S3
from app.config.s3 import s3_client
from app.db.crud.sign import (
    get_sign_by_id,
    get_signs_by_status,
    restore_sign,
    save_sign,
    soft_delete_sign,
    update_name,
)
from app.db.crud.user import get_user
from app.exception.custom_exception import AppException
from app.models.sign_style import SignatureStyle
from app.utils.cleanup import hard_delete_process
from app.utils.exception import raise_save_failed
from app.utils.s3 import generate_presigned_url, upload_sign


config = Config(".env")
logger = logging.getLogger(__name__)


def generate_sign_ai(
    name: str | None = None,
    style: SignatureStyle = SignatureStyle.LUXURY,
    seed: int | None = None,
):
    started_at = perf_counter()
    try:
        provider = get_sign_provider()
        logger.info(
            "sign.generate.provider.start provider=%s style=%s seed=%s",
            provider.name,
            style,
            seed,
        )
        sign_buffer = provider.generate(name or "Signature", style, seed)

        logger.info(
            "sign.generate.done style=%s seed=%s elapsed=%.2fs",
            style,
            seed,
            perf_counter() - started_at,
        )
        return sign_buffer
    except Exception as exc:
        logger.exception(
            "Signature generation failed. name=%s style=%s seed=%s",
            name,
            style,
            seed,
        )
        raise AppException(
            status=500,
            code=CODE.ERROR.GENERATE_FAILED,
            message=MESSAGE.ERROR.GENERATE_FAILED,
        ) from exc


def move_file_s3(
    temp_file_name: str, bucket: str, final_file_name: str
) -> bool:
    try:
        resource_s3 = boto3.resource(
            S3.ResourceName,
            aws_access_key_id=config("CREDENTIALS_ACCESS_KEY"),
            aws_secret_access_key=config("CREDENTIALS_SECRET_KEY"),
        )
        copy_source = {"Bucket": bucket, "Key": temp_file_name}

        resource_s3.meta.client.copy(copy_source, bucket, final_file_name)
        s3_client.delete_object(Bucket=bucket, Key=temp_file_name)
    except Exception as exc:
        raise_save_failed(exc)


def generate_filename() -> str:
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    return f"signature_{timestamp}"


async def save_sign_db(user_info, file_name, outline_file_name):
    user = await get_user(user_info=user_info)
    sign_name = generate_filename()

    await save_sign(user, file_name, sign_name, outline_file_name)


async def generate_sign_response(
    name: str | None,
    style: SignatureStyle,
    seed: int | None,
):
    request_id = uuid.uuid4().hex[:12]
    started_at = perf_counter()
    logger.info(
        "sign.request.start request_id=%s style=%s seed=%s",
        request_id,
        style,
        seed,
    )
    sign_buffer = generate_sign_ai(name, style, seed)
    user_info = "dev-local"
    file_name = f"temp/{user_info}/{uuid.uuid4().hex}.png"

    logger.info(
        "sign.request.upload.start request_id=%s file=%s",
        request_id,
        file_name,
    )
    upload_sign(
        buffer=sign_buffer, bucket=config("S3_BUCKET"), file_name=file_name
    )
    logger.info(
        "sign.request.upload.done request_id=%s file=%s elapsed=%.2fs",
        request_id,
        file_name,
        perf_counter() - started_at,
    )
    url = generate_presigned_url(file_name)

    logger.info(
        "sign.request.done request_id=%s file=%s elapsed=%.2fs",
        request_id,
        file_name,
        perf_counter() - started_at,
    )

    return {
        "status": 201,
        "code": CODE.SUCCESS.SIGN_GENERATION_SUCCESS,
        "message": MESSAGE.SUCCESS.SIGN_GENERATION_SUCCESS,
        "detail": url,
    }


async def finalize_sign_upload_response(temp_file_name: str, user):
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


async def get_signs_by_status_db(user_info, is_deleted):
    user = await get_user(user_info=user_info)

    return await get_signs_by_status(user, is_deleted)


def assert_sign_owner(sign, user):
    if (
        sign.user.social_id != user["social_id"]
        or sign.user.provider != user["provider"]
    ):
        raise AppException(
            status=403,
            code=CODE.ERROR.FORBIDDEN,
            message=MESSAGE.ERROR.FORBIDDEN,
        )


def serialize_sign(sign, include_url: bool = False) -> dict:
    response = {
        "id": str(sign.id),
        "name": sign.name,
        "fileName": sign.file_name,
        "createdAt": sign.created_at,
        "updatedAt": sign.updated_at,
        "isDeleted": sign.is_deleted,
        "deletedAt": sign.deleted_at,
    }

    if include_url:
        response["url"] = generate_presigned_url(sign.file_name)

    return response


async def get_signs_by_status_response(user_info, is_deleted):
    signs = await get_signs_by_status_db(user_info, is_deleted)

    return [serialize_sign(sign, include_url=True) for sign in signs]


async def get_owned_sign(user, sign_id: str):
    sign = await get_sign_by_id(sign_id)

    assert_sign_owner(sign, user)

    return sign


async def edit_name(user_info, sign_id, new_name):
    sign = await get_owned_sign(user_info, sign_id)

    return await update_name(str(sign.id), new_name)


async def edit_name_response(user_info, sign_id, new_name):
    edited_sign = await edit_name(user_info, sign_id, new_name)

    return {
        "id": str(edited_sign.id),
        "name": edited_sign.name,
        "updatedAt": edited_sign.updated_at,
    }


def extract_outline(buffer: io.BytesIO):
    image = Image.open(buffer).convert("L")
    cv_img = np.array(image)

    avg_brightness = np.mean(cv_img)
    is_clean_background = avg_brightness > 240

    if is_clean_background:
        _, binary = cv2.threshold(cv_img, 200, 255, cv2.THRESH_BINARY)
    else:
        blurred = cv2.GaussianBlur(cv_img, (7, 7), 1.5)
        binary = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            25,
            10,
        )
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    edges = cv2.Canny(binary, 50, 150)
    edges = cv2.bitwise_not(edges)
    outline_img = Image.fromarray(edges).convert("RGBA")
    datas = outline_img.getdata()
    new_data = [
        (0, 0, 0, 100) if item[:3] == (0, 0, 0) else (255, 255, 255, 0)
        for item in datas
    ]
    outline_img.putdata(new_data)

    output_buffer = io.BytesIO()
    outline_img.save(output_buffer, format="PNG")
    output_buffer.seek(0)

    return output_buffer


async def delete_sign_db(user, sign_id: str):
    sign = await get_owned_sign(user, sign_id)
    deleted_sign = await soft_delete_sign(sign)

    return deleted_sign


async def delete_sign_response(user, sign_id: str):
    deleted_sign = await delete_sign_db(user, sign_id)

    return serialize_sign(deleted_sign)


async def restore_sign_db(user, sign_id: str):
    sign = await get_sign_by_id(sign_id)

    if not sign:
        raise AppException(
            status=404,
            code=CODE.ERROR.ALREADY_DELETED,
            message=MESSAGE.ERROR.ALREADY_DELETED,
        )

    assert_sign_owner(sign, user)

    if not sign.is_deleted:
        raise AppException(
            status=400,
            code=CODE.ERROR.NOT_DELETED,
            message=MESSAGE.ERROR.NOT_DELETED,
        )

    restored_sign = await restore_sign(sign)

    return restored_sign


async def restore_sign_response(user, sign_id: str):
    restored_sign = await restore_sign_db(user, sign_id)

    return serialize_sign(restored_sign)


async def hard_delete_sign_db(user, sign_id: str):
    sign = await get_owned_sign(user, sign_id)

    file_name = sign.file_name

    await hard_delete_process(sign)

    return file_name


async def delete_sign_s3(file_name: str):
    s3_client.delete_object(Bucket=config("S3_BUCKET"), Key=file_name)


async def hard_delete_sign_response(user, sign_id: str):
    file_name = await hard_delete_sign_db(user, sign_id)

    await delete_sign_s3(file_name)

    return {
        "status": 200,
        "code": CODE.SUCCESS.HARD_DELETE,
        "message": MESSAGE.SUCCESS.HARD_DELETE,
    }


async def get_sign_url_response(user, sign_id: str):
    sign = await get_owned_sign(user, sign_id)

    return generate_presigned_url(sign.file_name)


async def get_sign_outline_response(
    user, sign_id: str, width: int, height: int
):
    sign = await get_owned_sign(user, sign_id)
    sign_url = generate_presigned_url(sign.file_name)
    skeleton_bytes = await get_skeleton_sign(sign_url, width, height)
    outline_url = generate_presigned_url(sign.outline_file_name)

    return {"url": outline_url, "skeleton": skeleton_bytes}


async def get_skeleton_sign(sign_url: str, width: int, height: int):
    response = requests.get(sign_url)

    if response.status_code != 200:
        raise AppException(
            status=500,
            code=CODE.ERROR.FETCH_FAILED,
            message=MESSAGE.ERROR.FETCH_FAILED,
        )

    byte_array = np.frombuffer(response.content, dtype=np.uint8)
    img = cv2.imdecode(byte_array, cv2.IMREAD_GRAYSCALE)

    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    skeleton = skeletonize(binary // 255).astype(np.uint8) * 255

    kernel = np.ones((3, 3), np.uint8)
    dilated_skeleton = cv2.dilate(skeleton, kernel, iterations=1)

    resized_skeleton = cv2.resize(
        dilated_skeleton, (width, height), interpolation=cv2.INTER_NEAREST
    )
    resized_skeleton = 255 - resized_skeleton

    _, buffer = cv2.imencode(".png", resized_skeleton)
    encoded_skeleton = base64.b64encode(buffer.tobytes()).decode("utf-8")

    return encoded_skeleton
