from jose.exceptions import ExpiredSignatureError, JWTError

from app.config.constants import CODE, MESSAGE
from app.exception.custom_exception import AppException


def handle_jwt_error(exc: Exception):
    if isinstance(exc, ExpiredSignatureError):
        raise AppException(
            401, CODE.ERROR.TOKEN_EXPIRED, MESSAGE.ERROR.UNAUTHORIZED
        ) from exc
    if isinstance(exc, JWTError):
        raise AppException(
            401, CODE.ERROR.TOKEN_INVALID, MESSAGE.ERROR.UNAUTHORIZED
        ) from exc
    raise AppException(
        500, CODE.ERROR.SERVER_ERROR, MESSAGE.ERROR.SERVER_ERROR
    ) from exc


def raise_save_failed(exc: Exception):
    raise AppException(
        status=500,
        code=CODE.ERROR.SAVE_FAILED,
        message=MESSAGE.ERROR.SAVE_FAILED,
    ) from exc
