from fastapi import Request

from app.config.constants import CODE, MESSAGE
from app.exception.custom_exception import AppException
from app.utils.jwt import decode_access_token
from app.utils.jwt_exception import handle_jwt_error


async def get_current_user(request: Request):
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise AppException(
            status=401,
            code=CODE.ERROR.NO_TOKEN,
            message=MESSAGE.ERROR.UNAUTHORIZED,
        )

    try:
        user_info = decode_access_token(access_token)

        return user_info
    except Exception as exc:
        handle_jwt_error(exc)
