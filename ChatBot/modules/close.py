import asyncio
from pyrogram import filters
from pyrogram.types import CallbackQuery
from ChatBot import app

@app.on_callback_query(filters.regex("close"))
async def close_button_handler(_, query: CallbackQuery):
    user = query.from_user

    try:
        await query.message.delete()
    except:
        pass

    try:
        msg = await query.message.reply(f"❌ Closed by: {user.mention}")
        await asyncio.sleep(5)
        await msg.delete()
    except:
        pass
