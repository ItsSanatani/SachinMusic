from . import authdb

async def add_auth(chat_id: int, user_id: int):
    user = await authdb.find_one({"chat_id": chat_id, "user_id": user_id})
    if not user:
        await authdb.insert_one({"chat_id": chat_id, "user_id": user_id})

async def remove_auth(chat_id: int, user_id: int):
    await authdb.delete_one({"chat_id": chat_id, "user_id": user_id})

async def get_auth_users(chat_id: int):
    users = await authdb.find({"chat_id": chat_id}).to_list(length=0)
    return [user["user_id"] for user in users]

async def is_auth(chat_id: int, user_id: int) -> bool:
    user = await authdb.find_one({"chat_id": chat_id, "user_id": user_id})
    return bool(user)
