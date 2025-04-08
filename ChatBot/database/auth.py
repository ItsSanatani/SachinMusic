from . import authdb

# Add auth user for specific group
async def add_auth(chat_id: int, user_id: int):
    user = await authdb.find_one({"chat_id": chat_id, "user_id": user_id})
    if not user:
        await authdb.insert_one({"chat_id": chat_id, "user_id": user_id})

# Remove auth user from specific group
async def remove_auth(chat_id: int, user_id: int):
    await authdb.delete_one({"chat_id": chat_id, "user_id": user_id})

# Get all auth users for a specific group
async def get_auth_users(chat_id: int):
    users = await authdb.find({"chat_id": chat_id}).to_list(length=0)
    return [user["user_id"] for user in users]

# Check if a user is authorized in a specific group
async def is_auth(chat_id: int, user_id: int) -> bool:
    user = await authdb.find_one({"chat_id": chat_id, "user_id": user_id})
    return bool(user)
