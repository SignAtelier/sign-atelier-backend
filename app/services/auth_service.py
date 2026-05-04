from datetime import datetime, timezone
import logging

from authlib.jose import JsonWebKey, JsonWebToken
import httpx
from starlette.config import Config

from app.config.constants import CODE, MESSAGE
from app.db.crud.user import get_user, upsert_user
from app.exception.custom_exception import AppException
from app.utils.exception import handle_jwt_error
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)


config = Config(".env")
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
logger = logging.getLogger(__name__)


async def create_google_refresh_token(userinfo: dict) -> str:
    user_data = await upsert_user(userinfo, "google")

    return create_user_refresh_token(user_data)


async def verify_google_credential(credential: str) -> dict:
    google_client_id = config("GOOGLE_CLIENT_ID")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(GOOGLE_JWKS_URL)
            response.raise_for_status()
            key_set = JsonWebKey.import_key_set(response.json())

        claims = JsonWebToken(["RS256"]).decode(credential, key_set)
        claims.validate(leeway=60)
    except Exception as exc:
        logger.exception("Google credential verification failed.")
        raise AppException(
            status=401,
            code=CODE.ERROR.NO_TOKEN,
            message=MESSAGE.ERROR.UNAUTHORIZED,
        ) from exc

    if claims.get("aud") != google_client_id:
        logger.warning(
            "Google credential audience mismatch. aud=%s expected=%s",
            claims.get("aud"),
            google_client_id,
        )
        raise AppException(
            status=401,
            code=CODE.ERROR.NO_TOKEN,
            message=MESSAGE.ERROR.UNAUTHORIZED,
        )

    if claims.get("iss") not in {
        "https://accounts.google.com",
        "accounts.google.com",
    }:
        logger.warning("Google credential issuer mismatch. iss=%s", claims.get("iss"))
        raise AppException(
            status=401,
            code=CODE.ERROR.NO_TOKEN,
            message=MESSAGE.ERROR.UNAUTHORIZED,
        )

    return {
        "sub": claims["sub"],
        "picture": claims.get("picture", ""),
    }


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
