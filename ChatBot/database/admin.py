from typing import Callable, Union
from functools import wraps

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, CallbackQuery

from ChatBot import app
from config import OWNER_ID

async def is_admins(chat_id: int, user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        print(f"[is_admins Error] {e}")
        return False

def admin_only(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(c: Client, m: Union[Message, CallbackQuery]):
        try:
            user_id = m.from_user.id
            if user_id == OWNER_ID:
                return await func(c, m)

            chat_id = m.message.chat.id if isinstance(m, CallbackQuery) else m.chat.id
            member = await c.get_chat_member(chat_id, user_id)

            if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                return await func(c, m)
            else:
                if isinstance(m, CallbackQuery):
                    await m.answer("Only admins can use this!", show_alert=True)
                else:
                    await m.reply_text("Only admins can use this!")
        except Exception as e:
            print(f"[admin_only Error] {e}")
    return wrapper
