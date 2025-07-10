from bson import ObjectId

from app.models.sign import Sign


async def save_sign(
    user, file_name: str, sign_name: str, outline_file_name: str
):
    sign = Sign(
        user=user,
        file_name=file_name,
        name=sign_name,
        outline_file_name=outline_file_name,
    )

    await sign.insert()


async def get_signs(user):
    return await Sign.find(Sign.user.id == user.id).to_list()


async def update_name(sign_id, new_name):
    object_id = ObjectId(sign_id)
    sign = await Sign.find_one(Sign.id == object_id)

    await sign.set({Sign.name: new_name})

    return sign
