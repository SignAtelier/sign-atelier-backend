from app.models.sign import Sign


async def save_sign(user, file_name: str):
    sign = Sign(user=user, file_name=file_name)

    await sign.insert()
