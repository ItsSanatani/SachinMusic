from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from ChatBot import app
from ChatBot.database.auth import add_auth_user, remove_auth_user
from ChatBot.database.admin import is_admins

auth_confirm_data = {}


@app.on_message(filters.command("auth") & filters.group)
async def add_auth(client, message: Message):
    if not await is_admins(message.chat.id, message.from_user.id):
        return await message.reply("❌ Only group owner or admins can use this command!")

    if not message.reply_to_message:
        return await message.reply("Reply to the user you want to authorize!")

    user_id = message.reply_to_message.from_user.id
    auth_confirm_data[message.id] = {"action": "add", "user_id": user_id}
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"auth_confirm:{message.id}:yes"),
            InlineKeyboardButton("❌ No", callback_data=f"auth_confirm:{message.id}:no")
        ]
    ])
    await message.reply(f"Do you want to **authorize** `{user_id}`?", reply_markup=keyboard)


@app.on_message(filters.command("rmauth") & filters.group)
async def remove_auth(client, message: Message):
    if not await is_admins(message.chat.id, message.from_user.id):
        return await message.reply("❌ Only group owner or admins can use this command!")

    if not message.reply_to_message:
        return await message.reply("Reply to the user you want to **unauthorize**!")

    user_id = message.reply_to_message.from_user.id
    auth_confirm_data[message.id] = {"action": "remove", "user_id": user_id}
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"auth_confirm:{message.id}:yes"),
            InlineKeyboardButton("❌ No", callback_data=f"auth_confirm:{message.id}:no")
        ]
    ])
    await message.reply(f"Do you want to **unauthorize** `{user_id}`?", reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"auth_confirm:(\d+):(yes|no)"))
async def confirm_auth_action(client, callback_query: CallbackQuery):
    _, msg_id, decision = callback_query.data.split(":")
    msg_id = int(msg_id)

    if msg_id not in auth_confirm_data:
        return await callback_query.answer("Confirmation expired or invalid!", show_alert=True)

    data = auth_confirm_data.pop(msg_id)

    if not await is_admins(callback_query.message.chat.id, callback_query.from_user.id):
        return await callback_query.answer("❌ Only admins can confirm!", show_alert=True)

    user_id = data["user_id"]

    if decision == "yes":
        if data["action"] == "add":
            await add_auth_user(user_id)
            await callback_query.message.edit_text(f"✅ `{user_id}` has been authorized.")
        else:
            await remove_auth_user(user_id)
            await callback_query.message.edit_text(f"❌ `{user_id}` has been unauthorized.")
    else:
        await callback_query.message.edit_text("❌ Action cancelled.")
