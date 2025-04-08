from pyrogram.types import ChatPrivileges, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid
from pyrogram import Client, filters, enums
from ChatBot import app
from functools import wraps
import logging


logging.basicConfig(level=logging.INFO)

pending_promotions = {}

def mention(user_id, name):
    return f"[{name}](tg://user?id={user_id})"

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


async def extract_user(message, client):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text("**❖ ᴘʟᴇᴀsᴇ ᴍᴇɴᴛɪᴏɴ ᴀ ᴜsᴇʀ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
            return None, None
        try:
            user = await client.get_users(args[1])
        except Exception:
            await message.reply_text("**❖ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ !!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
            return None, None
    return user.id, user.first_name

@app.on_message(filters.command(["admin", "promote"], prefixes=["/", "!", "%", ",", ".", "@", "#"]))
@admin_required
async def promote_handler(client, message):
    chat_id = message.chat.id
    user_id, first_name = await extract_user(message, client)
    if not user_id:
        return

    chat_member = await client.get_chat_member(chat_id, message.from_user.id)
    if not chat_member.privileges or not chat_member.privileges.can_promote_members:
        await message.reply_text("**❖ ʏᴏᴜ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ᴡɪᴛʜ 'ᴀᴅᴅ ᴀᴅᴍɪɴs ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ ᴜsᴇʀs !!**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
        return

    bot_member = await client.get_chat_member(chat_id, client.me.id)
    if not bot_member.privileges or not bot_member.privileges.can_promote_members:
        await message.reply_text("**❖ I ɴᴇᴇᴅ 'ᴀᴅᴅ ᴀᴅᴍɪɴs ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ ᴜsᴇʀs !!**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
        return

    user_member = await client.get_chat_member(chat_id, user_id)
    if user_member.privileges:
        await message.reply_text("**❖ ᴛʜɪs ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ !!**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
        return

    pending_promotions[message.from_user.id] = {
        "user_id": user_id,
        "first_name": first_name,
        "permissions": {
            "can_change_info": False,
            "can_delete_messages": False,
            "can_pin_messages": False,
            "can_invite_users": False,
            "can_restrict_members": False,
            "can_manage_video_chats": False,
            "can_promote_members": False
        }
    }

    await send_permission_keyboard(client, message, message.from_user.id)

async def send_permission_keyboard(client, message, admin_id, edit=False):
    permissions = pending_promotions[admin_id]["permissions"]
    
    def get_button(permission, text):
        status = "✅" if permissions[permission] else "❌"
        return InlineKeyboardButton(f"{status} {text}", callback_data=f"perm_{admin_id}_{permission}")

    keyboard = InlineKeyboardMarkup([
        [get_button("can_change_info", "ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɪɴғᴏ")],
        [get_button("can_delete_messages", "ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs")],
        [get_button("can_pin_messages", "ᴘɪɴ ᴍᴇssᴀɢᴇs")],
        [get_button("can_invite_users", "ɪɴᴠɪᴛᴇ ᴜsᴇʀs ᴠɪᴀ ʟɪɴᴋ")],
        [get_button("can_restrict_members", "ʙᴀɴ ᴜsᴇʀs")],
        [get_button("can_manage_video_chats", "ᴍᴀɴᴀɢᴇ ʟɪᴠᴇ sᴛʀᴇᴀᴍs")],
        [get_button("can_promote_members", "ᴀᴅᴅ ɴᴇᴡ ᴀᴅᴍɪɴ")],
        [InlineKeyboardButton("☑️ ᴄᴏɴғɪʀᴍ ᴘʀᴏᴍᴏᴛɪᴏɴ ☑️", callback_data=f"confirm_{admin_id}")]
    ])

    if edit:
        await message.edit_reply_markup(reply_markup=keyboard)
    else:
        await message.reply_text("**❖ ᴘʟᴇᴀsᴇ sᴇʟᴇᴄᴛ ᴛʜᴇ ᴘᴇʀᴍɪssɪᴏɴs ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɢʀᴀɴᴛ :**", reply_markup=keyboard)

@app.on_callback_query(filters.regex("^perm_|^confirm_"))
async def callback_handler(client, callback_query):
    try:
        data = callback_query.data
        admin_id = callback_query.from_user.id

        if data.startswith("perm_"):
            _, caller_id, permission = data.split("_", 2)
            if int(caller_id) != admin_id:
                await callback_query.answer("❖ ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ sᴇʟᴇᴄᴛ ᴛʜɪs ᴏᴘᴛɪᴏɴ !!", show_alert=True)
                return

            permissions = pending_promotions[admin_id]["permissions"]
            permissions[permission] = not permissions[permission]

            await callback_query.answer(f"❖ {permission.replace('_', ' ').title()} ʜᴀs ʙᴇᴇɴ sᴇᴛ !!")
            await send_permission_keyboard(client, callback_query.message, admin_id, edit=True)
        
        elif data.startswith("confirm_"):
            _, caller_id = data.split("_")
            if int(caller_id) != admin_id:
                await callback_query.answer("❖ ʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ !!", show_alert=True)
                return

            user_data = pending_promotions.pop(admin_id, None)
            if not user_data:
                await callback_query.answer("❖ sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ !!", show_alert=True)
                return

            user_id = user_data["user_id"]
            first_name = user_data["first_name"]
            permissions = user_data["permissions"]

            privileges = ChatPrivileges(
                can_change_info=permissions["can_change_info"],
                can_delete_messages=permissions["can_delete_messages"],
                can_pin_messages=permissions["can_pin_messages"],
                can_invite_users=permissions["can_invite_users"],
                can_restrict_members=permissions["can_restrict_members"],
                can_manage_video_chats=permissions["can_manage_video_chats"],
                can_promote_members=permissions["can_promote_members"],
                is_anonymous=False
            )

            try:
                await client.promote_chat_member(callback_query.message.chat.id, user_id, privileges)
                user_mention = mention(user_id, first_name)
                admin_mention = mention(admin_id, callback_query.from_user.first_name)
                await callback_query.message.edit_text(
                    f"**❖ ᴜsᴇʀ sᴜᴄᴄᴇssғᴜʟʟʏ ᴘʀᴏᴍᴏᴛᴇᴅ ➠**\n\n**● ᴘʀᴏᴍᴏᴛᴇᴅ ʙʏ :** {admin_mention} \n**● ᴜsᴇʀ :** {user_mention} !!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]]),)
                    
            except Exception as e:
                await callback_query.message.edit_text(f"❖ ᴘʀᴏᴍᴏᴛɪᴏɴ ғᴀɪʟᴇᴅ : {e}")
    except Exception as e:
        logging.error(f"Error in callback_handler: {e}")
