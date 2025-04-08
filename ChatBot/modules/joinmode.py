/eval from functools import wraps
from datetime import datetime
import pytz
from pyrogram import Client, filters, enums
from pyrogram.types import (
    ChatJoinRequest, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, Message
)
from pyrogram.errors import UserAlreadyParticipant, UserIsBlocked, PeerIdInvalid
from ChatBot import app
from config import MONGO_URL
from motor.motor_asyncio import AsyncIOMotorClient

mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["JoinRequestDB"]
joinmode_collection = db["JoinModes"]

async def is_joinmode_on(chat_id: int) -> bool:
    doc = await joinmode_collection.find_one({"chat_id": chat_id})
    return bool(doc and doc.get("enabled", False))

# Helper function: set joinmode
async def set_joinmode(chat_id: int, enabled: bool):
    await joinmode_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": enabled}},
        upsert=True
    )

def admin_required(func):
    @wraps(func)
    async def wrapper(client, message: Message):
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER] and getattr(member.privileges, 'can_restrict_members', False):
            return await func(client, message)
        else:
            await message.reply_text(
                "**❖ You don't have permission to perform this action!**",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]])
            )
    return wrapper

@app.on_message(filters.command("joiinmode") & filters.group)
@admin_required
async def toggle_join_mode(client, message: Message):
    await message.reply_text(
        "⚙️ sᴇʟᴇᴄᴛ ᴊᴏɪɴ ᴍᴏᴅᴇ :",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ ᴇɴᴀʙʟᴇ", callback_data="joinmode_on"),
                InlineKeyboardButton("❌ ᴅɪsᴀʙʟᴇ", callback_data="joinmode_off")
            ]
        ])
    )

@app.on_callback_query(filters.regex(r"joinmode_"))
async def joinmode_callback(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    member = await client.get_chat_member(chat_id, user_id)

    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        return await callback_query.answer("❌ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ.", show_alert=True)

    action = callback_query.data.split("_")[1]
    if action == "on":
        await set_joinmode(chat_id, True)
        await callback_query.edit_message_text("✅ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ sʏsᴛᴇᴍ ɪs ɴᴏᴡ *ᴇɴᴀʙʟᴇᴅ*.")
    elif action == "off":
        await set_joinmode(chat_id, False)
        await callback_query.edit_message_text("❌ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ sʏsᴛᴇᴍ ɪs ɴᴏᴡ *ᴅɪsᴀʙʟᴇᴅ*.")
