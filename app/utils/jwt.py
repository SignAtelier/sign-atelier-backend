from datetime import datetime, timedelta, timezone

from jose import jwt
from starlette.config import Config

config = Config(".env")


def create_jwt_token(
    data: dict, expires_minutes: timedelta = timedelta(hours=1)
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


def decode_jwt_token(access_token):
    payload = jwt.decode(
        access_token, config("SECRET_KEY"), algorithms=config("ALGORITHM")
    )
    user_info = {
        "social_id": payload.get("sub"),
        "provider": payload.get("provider"),
        "profile": payload.get("picture"),
    }

    return user_info
