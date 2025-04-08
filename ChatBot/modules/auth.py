from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from ChatBot import app
from ChatBot.database.auth import add_auth, remove_auth
from ChatBot.database.admin import is_admins

auth_confirm_data = {}

def format_user(user):
    username = f"@{user.username}" if user.username else "No Username"
    mention = user.mention(style="markdown")
    return f"**Name:** {mention}\n**User ID:** `{user.id}`\n**Username:** `{username}`"

async def get_target_user(message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    elif len(message.command) > 1:
        username = message.text.split(None, 1)[1].strip()
        try:
            user = await app.get_users(username)
            return user
        except:
            return None
    return None

@app.on_message(filters.command("auth") & filters.group)
async def add_auth_command(client, message: Message):
    if not await is_admins(message.chat.id, message.from_user.id):
        return await message.reply("❌ Only group owner or admins can use this command!")

    user = await get_target_user(message)
    if not user:
        return await message.reply("Reply to a user or give a valid username/user ID!")

    key = f"{message.chat.id}:{user.id}"
    auth_confirm_data[key] = {"action": "add", "chat_id": message.chat.id}

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"auth_confirm|{user.id}|yes"),
            InlineKeyboardButton("❌ No", callback_data=f"auth_confirm|{user.id}|no")
        ]
    ])

    await message.reply(
        f"Do you want to **authorize** this user?\n\n{format_user(user)}",
        reply_markup=keyboard
    )

@app.on_message(filters.command("rmauth") & filters.group)
async def remove_auth_command(client, message: Message):
    if not await is_admins(message.chat.id, message.from_user.id):
        return await message.reply("❌ Only group owner or admins can use this command!")

    user = await get_target_user(message)
    if not user:
        return await message.reply("Reply to a user or give a valid username/user ID!")

    key = f"{message.chat.id}:{user.id}"
    auth_confirm_data[key] = {"action": "remove", "chat_id": message.chat.id}

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"auth_confirm|{user.id}|yes"),
            InlineKeyboardButton("❌ No", callback_data=f"auth_confirm|{user.id}|no")
        ]
    ])

    await message.reply(
        f"Do you want to **unauthorize** this user?\n\n{format_user(user)}",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"^auth_confirm\|(\d+)\|(yes|no)$"))
async def confirm_auth_action(client, callback_query: CallbackQuery):
    parts = callback_query.data.split("|")
    if len(parts) != 3:
        return await callback_query.answer("Invalid data!", show_alert=True)

    user_id, decision = parts[1], parts[2]
    chat_id = callback_query.message.chat.id
    key = f"{chat_id}:{user_id}"

    data = auth_confirm_data.get(key)
    if not data:
        return await callback_query.answer("Confirmation expired or already used!", show_alert=True)

    if not await is_admins(chat_id, callback_query.from_user.id):
        return await callback_query.answer("❌ Only admins can confirm!", show_alert=True)

    del auth_confirm_data[key]

    if decision == "yes":
        if data["action"] == "add":
            await add_auth(int(user_id))
            await callback_query.message.edit_text(f"✅ User `{user_id}` has been **authorized**.")
        else:
            await remove_auth(int(user_id))
            await callback_query.message.edit_text(f"❌ User `{user_id}` has been **unauthorized**.")
    else:
        await callback_query.message.edit_text("❌ Action cancelled.")
