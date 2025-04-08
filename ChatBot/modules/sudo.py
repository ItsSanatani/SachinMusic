from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from ChatBot import app
from ChatBot.database.sudo import add_sudo, remove_sudo, get_sudoers
from config import OWNER_ID

sudo_confirm_data = {}


async def extract_user_id(message: Message) -> int:
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    if len(message.command) >= 2:
        user = message.command[1]
        if user.startswith("@"):
            try:
                user_obj = await message._client.get_users(user)
                return user_obj.id
            except Exception:
                return None
        else:
            try:
                return int(user)
            except ValueError:
                return None
    return None


@app.on_message(filters.command("addsudo") & filters.user(OWNER_ID))
async def addsudo_cmd(client, message):
    user_id = await extract_user_id(message)
    if not user_id:
        return await message.reply("Please specify a user to add to the SUDO list!")

    sudo_confirm_data[str(message.id)] = {"action": "add", "user_id": user_id}
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_sudo:{message.id}:yes"),
            InlineKeyboardButton("❌ No", callback_data=f"confirm_sudo:{message.id}:no")
        ]]
    )
    await message.reply(f"Do you want to add `{user_id}` to the SUDO list?", reply_markup=keyboard)


@app.on_message(filters.command("delsudo") & filters.user(OWNER_ID))
async def delsudo_cmd(client, message):
    user_id = await extract_user_id(message)
    if not user_id:
        return await message.reply("Please specify a user to remove from the SUDO list!")

    sudo_confirm_data[str(message.id)] = {"action": "remove", "user_id": user_id}
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_sudo:{message.id}:yes"),
            InlineKeyboardButton("❌ No", callback_data=f"confirm_sudo:{message.id}:no")
        ]]
    )
    await message.reply(f"Do you want to remove `{user_id}` from the SUDO list?", reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^confirm_sudo:(\d+):(yes|no)$"))
async def confirm_sudo_callback(client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split(":")
    if len(data_parts) != 3:
        return await callback_query.answer("Invalid data format!", show_alert=True)

    msg_id, decision = data_parts[1], data_parts[2]

    if callback_query.from_user.id != OWNER_ID:
        return await callback_query.answer("Only the OWNER can confirm this action!", show_alert=True)

    if msg_id not in sudo_confirm_data:
        return await callback_query.answer("Confirmation expired or invalid!", show_alert=True)

    data = sudo_confirm_data.pop(msg_id)
    user_id = data["user_id"]

    if decision == "yes":
        if data["action"] == "add":
            await add_sudo(user_id)
            await callback_query.message.edit_text(f"✅ `{user_id}` has been added to the SUDO list.")
        else:
            await remove_sudo(user_id)
            await callback_query.message.edit_text(f"❌ `{user_id}` has been removed from the SUDO list.")
    else:
        await callback_query.message.edit_text("❌ Action cancelled.")


@app.on_message(filters.command("sudolist"))
async def sudolist_cmd(client, message: Message):
    sudoers = await get_sudoers()
    
    if message.from_user.id not in sudoers:
        return await message.reply("❌ You are not authorized to view the SUDO list.")
    
    if not sudoers:
        return await message.reply("No SUDO users found.")

    text = "**SUDO Users:**\n\n"
    for uid in sudoers:
        try:
            user = await client.get_users(uid)
            name = f"{user.first_name} (`{user.id}`)"
        except:
            name = f"`{uid}`"
        text += f"• {name}\n"

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Close", callback_data="close")]]
    )

    await message.reply(text, reply_markup=keyboard)
