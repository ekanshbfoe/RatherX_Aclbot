from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.game_session import chat_id_to_instance, calculate_couples
from utils.formatting import format_mylove_dm

router = Router()

@router.message(Command("mylove"))
async def cmd_mylove(message: types.Message, bot: Bot):
    if message.chat.type == "private":
        await message.reply("⚠️ This command is for group chats! It finds your top match in the group.")
        return
        
    chat_id = message.chat.id
    chat_instance = chat_id_to_instance.get(chat_id)
    
    if not chat_instance:
        await message.reply("⚠️ I don't have enough local data for this group yet! Play a standard game with the /next command first so I can sync this chat.")
        return
        
    local_couples = calculate_couples("local", chat_instance)
    
    user_id = message.from_user.id
    my_matches = []
    
    for c in local_couples:
        if c["u1_id"] == user_id or c["u2_id"] == user_id:
            my_matches.append(c)
            
    if not my_matches:
        await message.reply("⚠️ You haven't answered enough common questions (5+) with anyone in this chat yet!")
        return
        
    text = format_mylove_dm(my_matches, user_id)
    
    try:
        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
        await message.reply("💌 I've sent your top matches to your DMs!")
    except TelegramForbiddenError:
        builder = InlineKeyboardBuilder()
        bot_me = await bot.get_me()
        builder.button(text="Start Bot", url=f"https://t.me/{bot_me.username}?start=love")
        
        await message.reply(
            f"Hey {message.from_user.first_name}! Start a chat with me privately first so I can send you your secret love stats.",
            reply_markup=builder.as_markup()
        )
