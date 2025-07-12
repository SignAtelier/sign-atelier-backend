from datetime import datetime, timedelta, timezone

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
    return (
        await Sign.find(Sign.user.id == user.id).sort("-created_at").to_list()
    )


async def get_sign_by_id(sign_id):
    object_id = ObjectId(sign_id)

    return await Sign.find_one(Sign.id == object_id, fetch_links=True)


async def update_name(sign_id, new_name):
    object_id = ObjectId(sign_id)
    sign = await Sign.find_one(Sign.id == object_id)

    await sign.set({Sign.name: new_name})

    return sign


async def soft_delete_sign(sign: Sign):
    sign.is_deleted = True
    sign.deleted_at = datetime.now(timezone.utc) + timedelta(days=30)

    await sign.save()

    return sign


async def restore_sign(sign: Sign):
    sign.is_deleted = False
    sign.deleted_at = None

    await sign.save()

    return sign
