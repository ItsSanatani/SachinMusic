from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
from ChatBot import app
from ChatBot.database.admin import is_admins

# Temporary memory to store what user selects
user_lock_selections = {}

LOCK_OPTIONS = {
    "text": "✏️ Text",
    "media": "📷 Media",
    "links": "🔗 Links",
    "other": "📎 Others",
}

# Function to create buttons with ✅ or ❌
def build_lock_buttons(chat_id, selected):
    buttons = []
    for key, label in LOCK_OPTIONS.items():
        emoji = "✅" if selected.get(key) else "❌"
        buttons.append([InlineKeyboardButton(f"{label} {emoji}", callback_data=f"toggle_{key}_{chat_id}")])
    buttons.append([InlineKeyboardButton("🔒 Confirm", callback_data=f"confirm_{chat_id}")])
    return InlineKeyboardMarkup(buttons)

# /lock command
@app.on_message(filters.command("lock") & filters.group)
async def lock_command(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not await is_admins(chat_id, user_id):
        return await message.reply("❌ You must be an admin to use this command.")

    user_lock_selections[user_id] = {key: False for key in LOCK_OPTIONS}

    await message.reply(
        "**Select what you want to lock:**",
        reply_markup=build_lock_buttons(chat_id, user_lock_selections[user_id])
    )

# Toggle selection on button click
@app.on_callback_query(filters.regex(r"toggle_(\w+)_(\d+)"))
async def toggle_lock_option(client, query: CallbackQuery):
    user_id = query.from_user.id
    lock_type, chat_id = query.data.split("_")[1:]
    chat_id = int(chat_id)

    if not await is_admins(chat_id, user_id):
        return await query.answer("You're not an admin!", show_alert=True)

    if user_id not in user_lock_selections:
        user_lock_selections[user_id] = {key: False for key in LOCK_OPTIONS}

    # Toggle current selection
    user_lock_selections[user_id][lock_type] = not user_lock_selections[user_id][lock_type]

    # Update buttons
    await query.edit_message_reply_markup(
        reply_markup=build_lock_buttons(chat_id, user_lock_selections[user_id])
    )

# Apply lock on Confirm
@app.on_callback_query(filters.regex(r"confirm_(\d+)"))
async def confirm_lock(client, query: CallbackQuery):
    chat_id = int(query.data.split("_")[1])
    user_id = query.from_user.id

    if not await is_admins(chat_id, user_id):
        return await query.answer("You're not an admin!", show_alert=True)

    selected = user_lock_selections.get(user_id, {})
    perms = ChatPermissions(
        can_send_messages=not selected.get("text", False),
        can_send_media_messages=not selected.get("media", False),
        can_add_web_page_previews=not selected.get("links", False),
        can_send_other_messages=not selected.get("other", False),
        can_send_polls=not selected.get("other", False)
    )

    try:
        await app.set_chat_permissions(chat_id, perms)
        await query.edit_message_text("✅ Selected permissions have been locked.")
    except Exception as e:
        await query.edit_message_text(f"⚠️ Failed to lock permissions: `{e}`")

    # Clear selection
    user_lock_selections.pop(user_id, None)

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
