from . import usersdb, chatsdb


async def get_chats() -> dict:
    """
    Fetch served users and chats from the database.
    Returns a dictionary containing lists of users and chats.
    """
    chats = []
    users = []

    async for chat in chatsdb.find({"chat_id": {"$lt": 0}}):
        chats.append(chat["chat_id"])

    async for user in usersdb.find({"user_id": {"$gt": 0}}):
        users.append(user["user_id"])

    return {
        "chats": chats,
        "users": users,
    }


async def add_user(user_id, username=None):
    """
    Adds or updates a user in the database.
    """
    await usersdb.update_one(
        {"user_id": user_id},
        {"$set": {"username": username}},
        upsert=True
    )


async def add_chat(chat_id, title=None):
    """
    Adds or updates a chat in the database.
    """
    await chatsdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"title": title}},
        upsert=True
    )
