from app.models.sign import Sign


async def save_sign(user, file_name: str, sign_name: str):
    sign = Sign(user=user, file_name=file_name, name=sign_name)

    await sign.insert()


async def get_signs(user):
    return await Sign.find(Sign.user.id == user.id).to_list()
