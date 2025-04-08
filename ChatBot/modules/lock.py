from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
from ChatBot import app
from ChatBot.database.admin import is_admins

# /lock command with buttons
@app.on_message(filters.command("lock") & filters.group)
async def lock_command(client, message: Message):
    if not await is_admins(message.chat.id, message.from_user.id):
        return await message.reply("❌ You must be an admin to use this command.")

    buttons = [
        [
            InlineKeyboardButton("✏️ Text", callback_data=f"lock_text_{message.chat.id}"),
        ],
        [
            InlineKeyboardButton("📷 Media", callback_data=f"lock_media_{message.chat.id}")
        ],
        [
            InlineKeyboardButton("🔗 Links", callback_data=f"lock_links_{message.chat.id}"),
        ],
        [
            InlineKeyboardButton("📎 Others", callback_data=f"lock_other_{message.chat.id}")
        ],
        [
            InlineKeyboardButton("🔒 Lock All", callback_data=f"lock_all_{message.chat.id}")
        ]
    ]

    await message.reply(
        "**Select what you want to lock:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Callback handler
@app.on_callback_query(filters.regex(r"lock_(\w+)_(\d+)"))
async def lock_callback(client, callback_query: CallbackQuery):
    data_type, chat_id = callback_query.data.split("_")[1:]
    chat_id = int(chat_id)
    user_id = callback_query.from_user.id

    if not await is_admins(chat_id, user_id):
        return await callback_query.answer("You're not an admin!", show_alert=True)

    perms = ChatPermissions()

    if data_type == "text":
        perms.can_send_messages = False
    elif data_type == "media":
        perms.can_send_media_messages = False
    elif data_type == "links":
        perms.can_add_web_page_previews = False
    elif data_type == "other":
        perms.can_send_other_messages = False
        perms.can_send_polls = False
    elif data_type == "all":
        # Remove all permissions
        perms = ChatPermissions()

    try:
        await app.set_chat_permissions(chat_id, perms)
        await callback_query.message.edit_text(f"✅ **Locked**: `{data_type}`", reply_markup=None)
    except Exception as e:
        await callback_query.message.edit_text(f"⚠️ Failed to apply lock: `{e}`")

 # /unlock command
@app.on_message(filters.command("unlock") & filters.group)
async def unlock_group(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_admins(chat_id, user_id):
        return await message.reply("❌ You must be an admin to use this command.")

    try:
        await app.set_chat_permissions(
            chat_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
            )
        )
        await message.reply("🔓 All group permissions have been unlocked. Members can chat freely now.")
    except Exception as e:
        await message.reply(f"⚠️ Failed to unlock the group: `{e}`") 
