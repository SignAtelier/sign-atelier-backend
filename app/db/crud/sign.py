from app.config.constants import CODE, MESSAGE
from app.exception.custom_exception import AppException
from app.models.sign import Sign
from app.models.user import User


async def save_sign(user, file_name: str):
    social_id = user["social_id"]
    provider = user["provider"]

    user = await User.find_one(
        User.social_id == social_id, User.provider == provider
    )

    if not user:
        raise AppException(
            status=404,
            code=CODE.ERROR.NOT_FOUND,
            message=MESSAGE.ERROR.NOT_FOUND,
        )

    sign = Sign(user=user, file_name=file_name)

    await sign.insert()
