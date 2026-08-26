from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.questions import get_random_question
from services.game_session import create_session
from utils.formatting import format_question_text

router = Router()

@router.message(Command("next"))
async def cmd_next(message: types.Message):
    question = get_random_question(nsfw=False)
    if not question:
        await message.reply("No SFW questions found in the database!")
        return

    # Build initial buttons
    builder = InlineKeyboardBuilder()
    builder.button(text="🔵", callback_data=f"vote_a_{question.id}")
    builder.button(text="🔴", callback_data=f"vote_b_{question.id}")
    builder.adjust(2)

    text = format_question_text(
        question.option_blue, 
        question.option_red
    )

    msg = await message.reply(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    
    game_id = f"{message.chat.id}_{msg.message_id}"
    create_session(game_id, question.id, is_nsfw=False)
