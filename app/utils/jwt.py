from datetime import datetime, timedelta, timezone

from jose import jwt
from starlette.config import Config

from app.config.constants import TOKEN

config = Config(".env")


def create_access_token(
    data: dict,
    expires_minutes: timedelta = TOKEN.EXPIRE.ACCESS,
):
    to_encode = data.copy()
    to_encode["exp"] = int(
        (
            datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        ).timestamp()
    )

    return jwt.encode(
        to_encode, config("SECRET_KEY"), algorithm=config("ALGORITHM")
    )


def create_refresh_token(
    data: dict,
    expires_hours: timedelta = TOKEN.EXPIRE.REFRESH,
):
    to_encode = data.copy()
    to_encode["exp"] = int(
        (
            datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        ).timestamp()
    )
    to_encode["type"] = "refresh"

    return jwt.encode(
        to_encode, config("SECRET_KEY"), algorithm=config("ALGORITHM")
    )


def decode_access_token(access_token):
    payload = jwt.decode(
        access_token, config("SECRET_KEY"), algorithms=config("ALGORITHM")
    )
    user_info = {
        "social_id": payload.get("sub"),
        "provider": payload.get("provider"),
        "profile": payload.get("picture"),
    }

    return user_info
