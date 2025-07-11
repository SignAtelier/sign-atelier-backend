from app.db.crud.practice import get_practice, save_practice


async def save_practice_db(file_name, sign_id):
    return await save_practice(file_name, sign_id)


async def get_practices_db(sign_id):
    return await get_practice(sign_id)
