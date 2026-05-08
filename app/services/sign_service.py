import asyncio
import base64
import io
import logging
import os
from datetime import datetime, timedelta, timezone
from time import perf_counter
from urllib.parse import unquote, urlparse
import uuid

import cv2
import httpx
import numpy as np
from PIL import Image
from skimage.morphology import skeletonize

from app.ai.providers import get_sign_provider
from app.config.constants import CODE, MESSAGE
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
from app.storage import get_storage
from app.utils.cleanup import hard_delete_process


logger = logging.getLogger(__name__)
_generation_semaphore = asyncio.Semaphore(1)


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


async def fetch_bytes(url: str) -> bytes:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        raise AppException(
            status=500,
            code=CODE.ERROR.FETCH_FAILED,
            message=MESSAGE.ERROR.FETCH_FAILED,
        ) from exc

    if response.status_code != 200:
        raise AppException(
            status=500,
            code=CODE.ERROR.FETCH_FAILED,
            message=MESSAGE.ERROR.FETCH_FAILED,
        )

    return response.content


def generate_filename() -> str:
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    return f"signature_{timestamp}"


async def save_sign_db(user_info, file_name, outline_file_name):
    user = await get_user(user_info=user_info)
    sign_name = generate_filename()

    await save_sign(user, file_name, sign_name, outline_file_name)


def normalize_storage_key(value: str) -> str:
    parsed = urlparse(value)
    key = unquote(parsed.path if parsed.scheme else value).lstrip("/")

    for bucket_name in (os.getenv("GCS_BUCKET"), os.getenv("S3_BUCKET")):
        if bucket_name and key.startswith(f"{bucket_name}/"):
            return key[len(bucket_name) + 1 :]

    return key


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
    async with _generation_semaphore:
        logger.info(
            "sign.request.ai_thread.start request_id=%s",
            request_id,
        )
        sign_buffer = await asyncio.to_thread(
            generate_sign_ai, name, style, seed
        )
        logger.info(
            "sign.request.ai_thread.done request_id=%s bytes=%s elapsed=%.2fs",
            request_id,
            sign_buffer.getbuffer().nbytes,
            perf_counter() - started_at,
        )
    file_name = f"temp/{uuid.uuid4().hex}.png"

    logger.info(
        "sign.request.upload.start request_id=%s file=%s",
        request_id,
        file_name,
    )
    storage = get_storage()

    await storage.upload(sign_buffer, file_name)
    logger.info(
        "sign.request.upload.done request_id=%s file=%s elapsed=%.2fs",
        request_id,
        file_name,
        perf_counter() - started_at,
    )
    logger.info(
        "sign.request.url.start request_id=%s file=%s",
        request_id,
        file_name,
    )
    url = await storage.generate_read_url(file_name)

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
    temp_file_name = normalize_storage_key(temp_file_name)
    final_file_name = temp_file_name.replace("temp", "signs", 1)
    storage = get_storage()

    logger.info(
        "sign.finalize.copy.start temp_file=%s final_file=%s",
        temp_file_name,
        final_file_name,
    )
    await storage.copy_and_delete(temp_file_name, final_file_name)
    logger.info(
        "sign.finalize.copy.done temp_file=%s final_file=%s",
        temp_file_name,
        final_file_name,
    )

    logger.info("sign.finalize.url.start file=%s", final_file_name)
    sign_url = await storage.generate_read_url(final_file_name)
    logger.info("sign.finalize.fetch.start file=%s", final_file_name)
    image_bytes = await fetch_bytes(sign_url)
    logger.info(
        "sign.finalize.fetch.done file=%s bytes=%s",
        final_file_name,
        len(image_bytes),
    )
    buffer = io.BytesIO(image_bytes)
    logger.info("sign.finalize.outline.start file=%s", final_file_name)
    outline_buffer = await asyncio.to_thread(extract_outline, buffer)
    logger.info(
        "sign.finalize.outline.done file=%s bytes=%s",
        final_file_name,
        outline_buffer.getbuffer().nbytes,
    )
    outline_file_name = final_file_name.replace("signs", "outline", 1)

    logger.info("sign.finalize.outline_upload.start file=%s", outline_file_name)
    await storage.upload(outline_buffer, outline_file_name)
    logger.info("sign.finalize.outline_upload.done file=%s", outline_file_name)
    logger.info("sign.finalize.db_save.start file=%s", final_file_name)
    await save_sign_db(user, final_file_name, outline_file_name)
    logger.info("sign.finalize.db_save.done file=%s", final_file_name)

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


def serialize_sign(sign) -> dict:
    return {
        "id": str(sign.id),
        "name": sign.name,
        "fileName": sign.file_name,
        "createdAt": sign.created_at,
        "updatedAt": sign.updated_at,
        "isDeleted": sign.is_deleted,
        "deletedAt": sign.deleted_at,
    }


async def get_signs_by_status_response(user_info, is_deleted):
    signs = await get_signs_by_status_db(user_info, is_deleted)
    storage = get_storage()
    response = []

    for sign in signs:
        item = serialize_sign(sign)
        item["url"] = await storage.generate_read_url(sign.file_name)
        response.append(item)

    return response


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
    await get_storage().delete(file_name)


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

    return await get_storage().generate_read_url(sign.file_name)


async def get_sign_outline_response(
    user, sign_id: str, width: int, height: int
):
    sign = await get_owned_sign(user, sign_id)
    storage = get_storage()
    sign_url = await storage.generate_read_url(sign.file_name)
    skeleton_bytes = await get_skeleton_sign(sign_url, width, height)
    outline_url = await storage.generate_read_url(sign.outline_file_name)

    return {"url": outline_url, "skeleton": skeleton_bytes}


async def get_skeleton_sign(sign_url: str, width: int, height: int):
    image_bytes = await fetch_bytes(sign_url)

    return await asyncio.to_thread(
        encode_skeleton_sign, image_bytes, width, height
    )


def encode_skeleton_sign(image_bytes: bytes, width: int, height: int):
    byte_array = np.frombuffer(image_bytes, dtype=np.uint8)
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
