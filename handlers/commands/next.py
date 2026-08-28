import time
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.questions import get_random_question
from services.game_session import create_session
from utils.formatting import format_question_text

router = Router()

_next_cooldowns: dict[int, float] = {}
NEXT_COOLDOWN_SECONDS = 10

@router.message(Command("next"))
async def cmd_next(message: types.Message):
    chat_id = message.chat.id
    now = time.time()
    
    # Rate limit: one /next per 10 seconds per chat
    last = _next_cooldowns.get(chat_id, 0)
    if now - last < NEXT_COOLDOWN_SECONDS:
        remaining = int(NEXT_COOLDOWN_SECONDS - (now - last))
        await message.reply(f"⏳ Please wait {remaining}s before starting a new game.")
        return
    
    _next_cooldowns[chat_id] = now
    
    question = get_random_question(nsfw=False)
    if not question:
        await message.reply("No SFW questions found in the database!")
        return

    # Build initial buttons
    builder = InlineKeyboardBuilder()
    builder.button(text="🔵", callback_data=f"vote:sfw:{question.id}:a")
    builder.button(text="🔴", callback_data=f"vote:sfw:{question.id}:b")
    builder.adjust(2)

    text = format_question_text(
        question.option_blue, 
        question.option_red
    )

    msg = await message.reply(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    
    game_id = f"{message.chat.id}:{msg.message_id}"
    create_session(game_id, question.id, is_nsfw=False)
