from datetime import datetime, timezone

from authlib.integrations.starlette_client import OAuthError
from fastapi import Request

from app.config.auth import oauth
from app.config.constants import CODE, MESSAGE
from app.db.crud.user import get_user, upsert_user
from app.exception.custom_exception import AppException
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.utils.jwt_exception import handle_jwt_error


async def handle_google_auth(userinfo: dict, provider: str) -> dict:
    user_data = await upsert_user(userinfo, provider)
    refresh_token = create_user_refresh_token(user_data)

    return refresh_token


async def fetch_google_userinfo(request: Request) -> str:
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        raise AppException(
            status=401,
            code=CODE.ERROR.NO_TOKEN,
            message=MESSAGE.ERROR.UNAUTHORIZED,
        ) from exc

    return token["userinfo"]


def create_user_access_token(user_data: dict) -> str:
    jwt_payload = {
        "sub": user_data["social_id"],
        "picture": user_data["profile"],
        "provider": user_data["provider"],
        "iss": "sign-atelier",
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }

    return create_access_token(data=jwt_payload)


def create_user_refresh_token(user_data: dict) -> str:
    payload = {
        "sub": user_data["social_id"],
        "provider": user_data["provider"],
        "iss": "sign-atelier",
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }

    return create_refresh_token(data=payload)


async def reissue_access_token(refresh_token: str) -> str:
    try:
        payload = decode_refresh_token(refresh_token)
    except Exception as exc:
        handle_jwt_error(exc)

    user = await get_user(payload)

    if not user:
        raise AppException(
            status=404,
            code=CODE.ERROR.NOT_FOUND,
            message=MESSAGE.ERROR.NOT_FOUND,
        )

    return create_user_access_token(user.model_dump())
