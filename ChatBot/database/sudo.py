from . import sudodb

async def add_sudo(user_id: int):
    """
    Add a user to sudoers.
    """
    if not await sudodb.find_one({"user_id": user_id}):
        await sudodb.insert_one({"user_id": user_id})

async def remove_sudo(user_id: int):
    """
    Remove a user from sudoers.
    """
    await sudodb.delete_one({"user_id": user_id})

async def get_sudoers() -> list:
    """
    Get a list of all sudo users.
    """
    sudoers = []
    async for user in sudodb.find({}):
        sudoers.append(user["user_id"])
    return sudoers

async def is_sudo(user_id: int) -> bool:
    """
    Check if a user is in sudo list.
    """
    return bool(await sudodb.find_one({"user_id": user_id}))
