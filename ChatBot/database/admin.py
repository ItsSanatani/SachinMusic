from typing import Callable, Union
from functools import wraps

from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, CallbackQuery
from pyrogram import Client


def is_admins(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(c: Client, m: Union[Message, CallbackQuery]):
        try:
            chat_id = m.message.chat.id if isinstance(m, CallbackQuery) else m.chat.id
            user_id = m.from_user.id

            member = await c.get_chat_member(chat_id, user_id)

            if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                return await func(c, m)
            else:
                if isinstance(m, CallbackQuery):
                    await m.answer("Only admins can use this!", show_alert=True)
                else:
                    await m.reply_text("Only admins can use this!")
        except Exception as e:
            print(f"[is_admins Error] {e}")

    return wrapper
