from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from pymongo import MongoClient

from ChatBot import app
from config import MONGO_URL, OTHER_LOGS
from ChatBot.database.auth import is_auth
from ChatBot.database.admin import is_admins

# Mongo Setup
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["copyright"]
settings_col = db["EditDeleteSettings"]

# Get current delete setting
def get_delete_status(chat_id):
    setting = settings_col.find_one({"chat_id": chat_id})
    return setting["delete_enabled"] if setting else True

# Set delete status
def set_delete_status(chat_id, status):
    settings_col.update_one({"chat_id": chat_id}, {"$set": {"delete_enabled": status}}, upsert=True)

# Command to toggle the edit delete feature
@app.on_message(filters.command("edit") & filters.group)
async def edit_toggle(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not await is_admins(chat_id, user_id):
        return await message.reply_text(
            "❖ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ !!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
        )

    try:
        bot_member = await client.get_chat_member(chat_id, client.me.id)
        if not bot_member.privileges or not bot_member.privileges.can_delete_messages:
            return await message.reply(
                f"<b>❖ {message.from_user.mention}, </b>\n\n"
                f"<b>๏ ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴅᴇʟᴇᴛᴇ ᴘᴇʀᴍɪssɪᴏɴ !!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
            )
    except:
        return

    status = "ON" if get_delete_status(chat_id) else "OFF"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴏɴ", callback_data="edit_on"),
         InlineKeyboardButton("ᴏғғ", callback_data="edit_off")],
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="edit_close")]
    ])
    await message.reply(f"❖ ᴇᴅɪᴛ ᴅᴇʟᴇᴛᴇ ғᴇᴀᴛᴜʀᴇ ɪs ᴄᴜʀʀᴇɴᴛʟʏ {status}.", reply_markup=keyboard)

# Handle button actions
@app.on_callback_query(filters.regex("^edit_"))
async def handle_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    data = callback_query.data

    if not await is_admins(chat_id, user_id):
        return await callback_query.answer("❖ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ !!", show_alert=True)

    if data == "edit_on":
        set_delete_status(chat_id, True)
        await callback_query.message.edit_text("<b>❖ ᴇᴅɪᴛ ᴅᴇʟᴇᴛᴇ ғᴇᴀᴛᴜʀᴇ ɪs ɴᴏᴡ ᴏɴ !!</b>")
    elif data == "edit_off":
        set_delete_status(chat_id, False)
        await callback_query.message.edit_text("<b>❖ ᴇᴅɪᴛ ᴅᴇʟᴇᴛᴇ ғᴇᴀᴛᴜʀᴇ ɪs ɴᴏᴡ ᴏғғ !!</b>")
    elif data == "edit_close":
        try:
            await callback_query.message.delete()
        except:
            pass

# Delete edited message if not admin/auth
@app.on_edited_message(filters.group & ~filters.me)
async def delete_edited_message(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if await is_admins(chat_id, user_id):
        return
    if await is_auth(chat_id, user_id):
        return
    if not get_delete_status(chat_id):
        return

    try:
        bot_member = await client.get_chat_member(chat_id, client.me.id)
        if not bot_member.privileges or not bot_member.privileges.can_delete_messages:
            return

        old_text = message.text or "❖ ɴᴏ ᴛᴇxᴛ ᴀᴠᴀɪʟᴀʙʟᴇ"
        await asyncio.sleep(2)
        await message.delete()

        log_text = (
            f"**❖ ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇ ᴅᴇʟᴇᴛᴇᴅ !!**\n\n"
            f"**๏ ᴜsᴇʀ :** {message.from_user.first_name} ({user_id})\n"
            f"**๏ ᴜsᴇʀɴᴀᴍᴇ :** @{message.from_user.username if message.from_user.username else 'ɴᴏɴᴇ'}\n"
            f"**๏ ᴍᴇɴᴛɪᴏɴ :** {message.from_user.mention}\n"
            f"**๏ ɢʀᴏᴜᴘ :** {message.chat.title}\n"
            f"**๏ ᴄʜᴀᴛ ɪᴅ :** ({chat_id})\n"
            f"**๏ ᴏʟᴅ ᴍᴇssᴀɢᴇ :**`{old_text}`\n"
            f"**๏ ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇ :**`{message.text}`\n\n"
            f"**❖ ʙᴏᴛ ɴᴀᴍᴇ :  @{app.username} **"
        )

        await client.send_message(OTHER_LOGS, log_text)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="edit_close")]
        ])
        await message.reply(
            f"<b>❖ ʜᴇʏ , {message.from_user.mention} !! </b>\n"
            f"<b>๏ ʏᴏᴜ ᴇᴅɪᴛᴇᴅ ᴀ ᴍᴇssᴀɢᴇ, sᴏ ɪ ᴅᴇʟᴇᴛᴇᴅ ɪᴛ !!</b>\n\n"
            f"<b>❖ ᴏɴ|ᴏғғ ᴄᴍᴍɴᴅ : /edit</b>\n"
            f"<b>❖ ʟᴏɢs : [ʏᴏᴜʀ ʙɪᴏ ʟᴏɢs](https://t.me/YourLogger)</b>",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"[EditDelete Error] {e}")
