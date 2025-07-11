from app.db.crud.practice import save_practice
from app.db.crud.user import get_user


async def save_practice_db(user_info, file_name, sign_id):
    await get_user(user_info=user_info)

    await save_practice(file_name, sign_id)
