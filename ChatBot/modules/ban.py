from pyrogram import Client, filters, enums
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid, UserNotParticipant
from functools import wraps
from SachinMusic import app

def mention(user_id, name):
    return f"{name}"

def admin_required(func):
    @wraps(func)
    async def wrapper(client, message):
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER] and member.privileges.can_restrict_members:
            return await func(client, message)
        else:
            await message.reply_text("**❖ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴘᴇʀғᴏʀᴍ ᴛʜɪs ᴀᴄᴛɪᴏɴ !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
    return wrapper

async def extract_user_and_reason(message, client):
    args = message.text.split(maxsplit=2)  
    user = None
    reason = None

    if message.reply_to_message:  
        user = message.reply_to_message.from_user  
        if len(args) > 1:
            reason = args[1]  
    elif len(args) > 1:
        user_arg = args[1]
        reason = args[2] if len(args) > 2 else None
        try:
            user = await client.get_users(user_arg)  
        except Exception:
            await message.reply_text(
                "**❖ ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ !!**",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]),
            )
            return None, None, None  

    if not user:  
        await message.reply_text(
            "**❖ ᴘʟᴇᴀsᴇ ᴍᴇɴᴛɪᴏɴ ᴀ ᴠᴀʟɪᴅ ᴜsᴇʀ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇɪʀ ᴍᴇssᴀɢᴇ !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]),
        )
        return None, None, None  

    try:
        chat_member = await client.get_chat_member(message.chat.id, user.id)
    except UserNotParticipant:
        await message.reply_text(
            "**❖ ᴛʜɪs ᴜsᴇʀ ɪs ɴᴏᴛ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]),
        )
        return None, None, None  

    if chat_member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        await message.reply_text(
            "**❖ ᴛʜɪs ᴜsᴇʀ ɪs ᴀ sᴛᴀғғ ᴍᴇᴍʙᴇʀ ᴀɴᴅ ᴄᴀɴɴᴏᴛ ʙᴇ ᴍᴜᴛᴇᴅ ᴏʀ ʙᴀɴɴᴇᴅ !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]),
        )
        return None, None, None  

    return user.id, user.first_name, reason
    
@app.on_message(filters.command("ban", prefixes=["/", "!", "%", ",", ".", "@", "#"]))
@admin_required
async def ban_command_handler(client, message):
    user_id, first_name, reason = await extract_user_and_reason(message, client)
    if not user_id:
        return
    
    try:
        chat_member = await client.get_chat_member(message.chat.id, user_id)
        if chat_member.status == enums.ChatMemberStatus.BANNED:
            await message.reply_text("**❖ ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ʙᴀɴɴᴇᴅ !!**",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]))
            return

        await client.ban_chat_member(message.chat.id, user_id)
        user_mention = mention(user_id, first_name)
        admin_mention = mention(message.from_user.id, message.from_user.first_name)
        msg = f"**❖ ᴜsᴇʀ sᴜᴄᴄᴇssғᴜʟʟʏ ʙᴀɴɴᴇᴅ ➠**\n\n**● ʙᴀɴɴᴇᴅ ʙʏ :** {admin_mention}\n**● ᴜsᴇʀ :** {user_mention}"
        
        if reason:
            msg += f"\n\n**● ʀᴇᴀsᴏɴ :** {reason}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴜɴʙᴀɴ", callback_data=f"unban_{user_id}")],
            [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
        ])
        await message.reply_text(msg, reply_markup=keyboard)
    except ChatAdminRequired:
        await message.reply_text("**❖ ɪ ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ᴡɪᴛʜ ʙᴀɴ ᴘᴇʀᴍɪssɪᴏɴs !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]))

@app.on_callback_query(filters.regex(r"^unban_(\d+)$"))
async def unban_callback(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    chat_id = callback_query.message.chat.id
    from_user = callback_query.from_user  

    chat_member = await client.get_chat_member(chat_id, from_user.id)
    if chat_member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        return await callback_query.answer("**❖ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ !!**", show_alert=True)

    try:
        await client.unban_chat_member(chat_id, user_id)
        await callback_query.message.edit_text(f"**❖ ᴜsᴇʀ ᴜɴʙᴀɴɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]),
        )
    except Exception:
        await callback_query.answer("❖ ғᴀɪʟᴇᴅ ᴛᴏ ᴜɴʙᴀɴ ᴛʜᴇ ᴜsᴇʀ !!", show_alert=True)


@app.on_message(filters.command("unban", prefixes=["/", "!", "%", ",", ".", "@", "#"]))
@admin_required
async def unban_user(client, message):
    user_id, first_name, _ = await extract_user_and_reason(message, client)
    if not user_id:
        return

    try:
        chat_member = await client.get_chat_member(message.chat.id, user_id)
        if chat_member.status != enums.ChatMemberStatus.BANNED:
            await message.reply_text("❖ ᴜsᴇʀ ɪs ɴᴏᴛ ʙᴀɴɴᴇᴅ !!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
            return

        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply_text(f"**❖ {mention(user_id, first_name)} ʜᴀs ʙᴇᴇɴ sᴜᴄᴄᴇssғᴜʟʟʏ ᴜɴʙᴀɴɴᴇᴅ !!**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
    except ChatAdminRequired:
        await message.reply_text("**❖ ɪ ɴᴇᴇᴅ ᴀᴅᴍɪɴ ᴘʀɪᴠɪʟᴇɢᴇs ᴛᴏ ᴜɴʙᴀɴ ᴜsᴇʀs !!**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
        
@app.on_message(filters.command("mute", prefixes=["/", "!", "%", ",", ".", "@", "#"]))
@admin_required
async def mute_command_handler(client, message):
    user_id, first_name, reason = await extract_user_and_reason(message, client)
    if not user_id:
        return

    try:
        chat_member = await client.get_chat_member(message.chat.id, user_id)
        if chat_member.status == enums.ChatMemberStatus.RESTRICTED:
            await message.reply_text("**❖ ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴍᴜᴛᴇᴅ !!**",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]))
            return

        await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions())
        user_mention = mention(user_id, first_name)
        admin_mention = mention(message.from_user.id, message.from_user.first_name)
        msg = f"**❖ ᴜsᴇʀ sᴜᴄᴄᴇssғᴜʟʟʏ ᴍᴜᴛᴇᴅ ➠**\n\n**● ᴍᴜᴛᴇᴅ ʙʏ :** {admin_mention}\n**● ᴜsᴇʀ :** {user_mention}"
        
        if reason:
            msg += f"\n\n**● ʀᴇᴀsᴏɴ :** {reason}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴜɴᴍᴜᴛᴇ", callback_data=f"unmute_{user_id}")],
            [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
        ])
        await message.reply_text(msg, reply_markup=keyboard)
    except ChatAdminRequired:
        await message.reply_text("**❖ ɪ ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ᴡɪᴛʜ ᴍᴜᴛᴇ ᴘᴇʀᴍɪssɪᴏɴs !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]))

@app.on_callback_query(filters.regex(r"^unmute_(\d+)$"))
async def unmute_callback(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    chat_id = callback_query.message.chat.id
    from_user = callback_query.from_user  

    chat_member = await client.get_chat_member(chat_id, from_user.id)
    if chat_member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        return await callback_query.answer("❖ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ !!", show_alert=True)

    try:
        await client.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=True))
        await callback_query.message.edit_text(f"**❖ ᴜsᴇʀ ᴜɴᴍᴜᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]),
        )
    except Exception:
        await callback_query.answer("❖ ғᴀɪʟᴇᴅ ᴛᴏ ᴜɴᴍᴜᴛᴇ ᴛʜᴇ ᴜsᴇʀ !!", show_alert=True)


@app.on_message(filters.command("unmute", prefixes=["/", "!", "%", ",", ".", "@", "#"]))
@admin_required
async def unmute_user(client, message):
    user_id, first_name, _ = await extract_user_and_reason(message, client)
    if not user_id:
        return

    try:
        chat_member = await client.get_chat_member(message.chat.id, user_id)
        if chat_member.status != enums.ChatMemberStatus.RESTRICTED:
            await message.reply_text("**❖ ᴜsᴇʀ ɪs ɴᴏᴛ ᴍᴜᴛᴇᴅ !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
            return

        await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=True))
        await message.reply_text(f"**❖ {mention(user_id, first_name)} ʜᴀs ʙᴇᴇɴ sᴜᴄᴄᴇssғᴜʟʟʏ ᴜɴᴍᴜᴛᴇᴅ !!**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
    except ChatAdminRequired:
        await message.reply_text("**❖ ɪ ɴᴇᴇᴅ ᴀᴅᴍɪɴ ᴘʀɪᴠɪʟᴇɢᴇs ᴛᴏ ᴜɴᴍᴜᴛᴇ ᴜsᴇʀs !!**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
