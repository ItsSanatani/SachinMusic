from ChatBot import db

authdb = db.authusers

async def add_auth(user_id: int):
    user = await authdb.find_one({"user_id": user_id})
    if not user:
        await authdb.insert_one({"user_id": user_id})

async def remove_auth(user_id: int):
    await authdb.delete_one({"user_id": user_id})

async def get_auth_users():
    users = await authdb.find().to_list(length=0)
    return [user["user_id"] for user in users]

async def is_auth(user_id: int) -> bool:
    user = await authdb.find_one({"user_id": user_id})
    return bool(user)
