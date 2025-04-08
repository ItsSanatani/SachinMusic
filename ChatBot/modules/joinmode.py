from functools import wraps
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
from ChatBot.database.admin import is_admins

mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["JoinRequestDB"]
joinmode_collection = db["JoinModes"]

# Check if joinmode is enabled
async def is_joinmode_on(chat_id: int) -> bool:
    doc = await joinmode_collection.find_one({"chat_id": chat_id})
    return bool(doc and doc.get("enabled", False))

# Set joinmode ON/OFF
async def set_joinmode(chat_id: int, enabled: bool):
    await joinmode_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": enabled}},
        upsert=True
    )

@app.on_message(filters.command("joinmode") & filters.group)
@is_admins
async def toggle_join_mode(client, message: Message):
    await message.reply_text(
        "⚙️ ᴊᴏɪɴ ᴍᴏᴅᴇ ᴍᴇɴᴜ:",
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
        return await callback_query.answer("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ.", show_alert=True)

    action = callback_query.data.split("_")[1]
    if action == "on":
        await set_joinmode(chat_id, True)
        await callback_query.edit_message_text("✅ ᴊᴏɪɴ ᴍᴏᴅᴇ ɪs *ᴇɴᴀʙʟᴇᴅ*.")
    elif action == "off":
        await set_joinmode(chat_id, False)
        await callback_query.edit_message_text("❌ ᴊᴏɪɴ ᴍᴏᴅᴇ ɪs *ᴅɪsᴀʙʟᴇᴅ*.")

@app.on_chat_join_request()
async def handle_join_request(client, request: ChatJoinRequest):
    if not await is_joinmode_on(request.chat.id):
        return

    # Timezone: India
    india_tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india_tz)
    current_time = now.strftime("%I:%M:%S %p")
    current_date = now.strftime("%d-%m-%Y")

    user = request.from_user
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "N/A"
    mention = user.mention
    chat_title = request.chat.title

    try:
        await client.send_message(
            user.id,
            f"📥 ʏᴏᴜ ʀᴇǫᴜᴇsᴛᴇᴅ ᴛᴏ ᴊᴏɪɴ <b>{chat_title}</b>.\nᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ғᴏʀ ᴀᴅᴍɪɴ ᴀᴘᴘʀᴏᴠᴀʟ.",
        )
    except (UserIsBlocked, PeerIdInvalid):
        pass

    await client.send_message(
        request.chat.id,
        f"🔔 <b>Join Request</b>\n\n"
        f"👤 <b>Name:</b> {full_name}\n"
        f"📛 <b>Username:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"🔗 <b>Mention:</b> {mention}\n"
        f"⏰ <b>Time:</b> {current_time}\n"
        f"📅 <b>Date:</b> {current_date}\n"
        f"👥 <b>Group:</b> {chat_title}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"decline_{user.id}")
            ]
        ])
    )

@app.on_callback_query(filters.regex(r"^approve_"))
async def approve_callback(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = int(callback_query.data.split("_")[1])
    member = await client.get_chat_member(chat_id, callback_query.from_user.id)

    privileges = getattr(member, 'privileges', None)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER] or not getattr(privileges, 'can_invite_users', True):
        return await callback_query.answer("❌ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴀᴘᴘʀᴏᴠᴇ.", show_alert=True)

    try:
        await client.approve_chat_join_request(chat_id, user_id)
        await callback_query.message.edit(f"✅ Approved by {callback_query.from_user.mention}")
        try:
            await client.send_message(user_id, f"✅ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {callback_query.message.chat.title} ɪs ᴀᴄᴄᴇᴘᴛᴇᴅ.")
        except:
            pass
    except UserAlreadyParticipant:
        await callback_query.message.edit("⚠️ Already in the group.")
    except Exception as e:
        await callback_query.message.edit(f"❌ Error: {e}")

@app.on_callback_query(filters.regex(r"^decline_"))
async def decline_callback(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = int(callback_query.data.split("_")[1])
    member = await client.get_chat_member(chat_id, callback_query.from_user.id)

    privileges = getattr(member, 'privileges', None)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER] or not getattr(privileges, 'can_invite_users', True):
        return await callback_query.answer("❌ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴅᴇᴄʟɪɴᴇ.", show_alert=True)

    try:
        await client.decline_chat_join_request(chat_id, user_id)
        await callback_query.message.edit(f"❌ Declined by {callback_query.from_user.mention}")
        try:
            await client.send_message(user_id, f"❌ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {callback_query.message.chat.title} ʜᴀs ʙᴇᴇɴ ʀᴇᴊᴇᴄᴛᴇᴅ.")
        except:
            pass
    except UserAlreadyParticipant:
        await callback_query.message.edit("⚠️ Already in the group.")
    except Exception as e:
        await callback_query.message.edit(f"❌ Error: {e}")
