from fastapi import Request
from jose.exceptions import ExpiredSignatureError, JWTError

from app.config.constants import CODE, MESSAGE
from app.exception.custom_exception import AppException
from app.utils.jwt import decode_jwt_token


async def get_current_user(request: Request):
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise AppException(
            status=401,
            code=CODE.ERROR.NO_TOKEN,
            message=MESSAGE.ERROR.UNAUTHORIZED,
        )

    try:
        user_info = decode_jwt_token(access_token)

        return user_info
    except ExpiredSignatureError as exc:
        raise AppException(
            status=401,
            code=CODE.ERROR.TOKEN_EXPIRED,
            message=MESSAGE.ERROR.UNAUTHORIZED,
        ) from exc
    except JWTError as exc:
        raise AppException(
            status=401,
            code=CODE.ERROR.TOKEN_INVALID,
            message=MESSAGE.ERROR.UNAUTHORIZED,
        ) from exc
    except Exception as exc:
        raise AppException(
            status=500,
            code=CODE.ERROR.SERVER_ERROR,
            message=MESSAGE.ERROR.SERVER_ERROR,
        ) from exc
