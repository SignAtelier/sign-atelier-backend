from typing import Annotated

from fastapi import Header

from app.config.constants import CODE, MESSAGE
from app.exception.custom_exception import AppException
from app.utils.jwt import decode_access_token
from app.utils.jwt_exception import handle_jwt_error


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
):
    if not authorization or not authorization.startswith("Bearer "):
        raise AppException(
            status=401,
            code=CODE.ERROR.NO_TOKEN,
            message=MESSAGE.ERROR.UNAUTHORIZED,
        )

    access_token = authorization.replace("Bearer ", "")

    try:
        user_info = decode_access_token(access_token)

        return {
            "social_id": user_info["social_id"],
            "provider": user_info["provider"],
            "profile": user_info["profile"],
        }
    except Exception as exc:
        handle_jwt_error(exc)
