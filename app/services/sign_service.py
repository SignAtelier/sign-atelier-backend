import base64
import io
from datetime import datetime, timedelta, timezone

import boto3
import cv2
import numpy as np
import requests
from PIL import Image
from skimage.morphology import skeletonize
from starlette.config import Config

from app.ai.generate_sign import generate_signature
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
from app.utils.cleanup import hard_delete_process
from app.utils.exception import raise_save_failed


config = Config(".env")


def generate_sign_ai(name: str, image_bytes: io.BytesIO):
    try:
        sign_buffer = generate_signature(name, image_bytes)

        return sign_buffer
    except Exception as exc:
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


async def get_signs_by_status_db(user_info, is_deleted):
    user = await get_user(user_info=user_info)

    return await get_signs_by_status(user, is_deleted)


async def edit_name(user_info, sign_id, new_name):
    await get_user(user_info=user_info)

    return await update_name(sign_id, new_name)


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
    sign = await get_sign_by_id(sign_id)

    if (
        not sign.user.social_id == user["social_id"]
        and not sign.user.provider == user["provider"]
    ):
        raise AppException(
            status=403,
            code=CODE.ERROR.FORBIDDEN,
            message=MESSAGE.ERROR.FORBIDDEN,
        )

    deleted_sign = await soft_delete_sign(sign)

    return deleted_sign


async def restore_sign_db(user, sign_id: str):
    sign = await get_sign_by_id(sign_id)

    if not sign:
        raise AppException(
            status=404,
            code=CODE.ERROR.ALREADY_DELETED,
            message=MESSAGE.ERROR.ALREADY_DELETED,
        )

    if (
        not sign.user.social_id == user["social_id"]
        and not sign.user.provider == user["provider"]
    ):
        raise AppException(
            status=403,
            code=CODE.ERROR.FORBIDDEN,
            message=MESSAGE.ERROR.FORBIDDEN,
        )

    if not sign.is_deleted:
        raise AppException(
            status=400,
            code=CODE.ERROR.NOT_DELETED,
            message=MESSAGE.ERROR.NOT_DELETED,
        )

    restored_sign = await restore_sign(sign)

    return restored_sign


async def hard_delete_sign_db(sign_id: str):
    sign = await get_sign_by_id(sign_id)

    file_name = sign.file_name

    await hard_delete_process(sign)

    return file_name


async def delete_sign_s3(file_name: str):
    s3_client.delete_object(Bucket=config("S3_BUCKET"), Key=file_name)


async def get_sign_one(sign_id: str):
    return await get_sign_by_id(sign_id)


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
