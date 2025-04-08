from functools import wraps
from datetime import datetime
import pytz
from pyrogram import Client, filters, enums
from pyrogram.types import (
    ChatJoinRequest, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, Message
)
from pyrogram.errors import UserAlreadyParticipant, UserIsBlocked, PeerIdInvalid
from SachinMusic import app
from config import MONGO_DB_URI
from motor.motor_asyncio import AsyncIOMotorClient
from ChatBot.database.admin import is_admin

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
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

@app.on_message(filters.command("joinmode") & filters.group)
@is_admin
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
        
# Handle join requests
@app.on_chat_join_request()
async def handle_join_request(client, request: ChatJoinRequest):
    if not await is_joinmode_on(request.chat.id):
        return

    # Timezone set to India
    india_tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india_tz)
    current_time = now.strftime("%I:%M:%S %p")
    current_date = now.strftime("%d-%m-%Y")

    user = request.from_user
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "N/A"
    user_id = user.id
    mention = user.mention
    group_name = request.chat.title

    try:
        await client.send_message(
            user.id,
            f"📥 ʏᴏᴜ ʀᴇǫᴜᴇsᴛᴇᴅ ᴛᴏ ᴊᴏɪɴ <b>{group_name}</b>.\nᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ғᴏʀ ᴀᴅᴍɪɴ ᴀᴘᴘʀᴏᴠᴀʟ.",
        )
    except (UserIsBlocked, PeerIdInvalid):
        pass

    await client.send_message(
        request.chat.id,
        f"🔔 <b>Join Request</b>\n\n"
        f"👤 <b>ᴜsᴇʀ ɴᴀᴍᴇ:</b> {full_name}\n"
        f"📛 <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {username}\n"
        f"🆔 <b>ᴜsᴇʀ ɪᴅ:</b> <code>{user_id}</code>\n"
        f"🔗 <b>ᴍᴇɴᴛɪᴏɴ:</b> {mention}\n"
        f"⏰ <b>ᴛɪᴍᴇ:</b> {current_time}\n"
        f"📅 <b>ᴅᴀᴛᴇ:</b> {current_date}\n"
        f"👥 <b>ɢʀᴏᴜᴘ ɴᴀᴍᴇ:</b> {group_name}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ ᴀᴘᴘʀᴏᴠᴇ", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("❌ ᴅᴇᴄʟɪɴᴇ", callback_data=f"decline_{user_id}")
            ]
        ])
    )

@app.on_callback_query(filters.regex(r"^approve_"))
async def approve_callback(client, callback_query: CallbackQuery):
    member = await client.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER] or not getattr(member.privileges, 'can_invite_users', False):
        return await callback_query.answer("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴀᴘᴘʀᴏᴠᴇ ʀᴇǫᴜᴇsᴛs.", show_alert=True)

    user_id = int(callback_query.data.split("_")[1])
    try:
        await client.approve_chat_join_request(callback_query.message.chat.id, user_id)
        await callback_query.message.edit(f"✅ ᴀᴘᴘʀᴏᴠᴇᴅ ʙʏ {callback_query.from_user.mention}")
        try:
            await client.send_message(user_id, f"✅ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {callback_query.message.chat.title} ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ!")
        except:
            pass
    except UserAlreadyParticipant:
        await callback_query.message.edit("⚠️ ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ.")
    except Exception as e:
        await callback_query.message.edit(f"❌ Error: {e}")

@app.on_callback_query(filters.regex(r"^decline_"))
async def decline_callback(client, callback_query: CallbackQuery):
    member = await client.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER] or not getattr(member.privileges, 'can_invite_users', False):
        return await callback_query.answer("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴅᴇᴄʟɪɴᴇ ʀᴇǫᴜᴇsᴛs.", show_alert=True)

    user_id = int(callback_query.data.split("_")[1])
    try:
        await client.decline_chat_join_request(callback_query.message.chat.id, user_id)
        await callback_query.message.edit(f"❌ Declined by {callback_query.from_user.mention}")
        try:
            await client.send_message(user_id, f"❌ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {callback_query.message.chat.title} ʜᴀs ʙᴇᴇɴ ᴅᴇᴄʟɪɴᴇᴅ.")
        except:
            pass
    except UserAlreadyParticipant:
        await callback_query.message.edit("⚠️ ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ.")
    except Exception as e:
        await callback_query.message.edit(f"❌ Error: {e}")
