from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database.questions import get_random_question
from services.game_session import create_session
from utils.formatting import format_question_text, get_voting_keyboard

router = Router()

@router.message(Command("next"))
async def cmd_next(message: Message):
    question = get_random_question(nsfw=False)
    
    # We will temporarily use a placeholder game_id and update it once we send the message
    # so we know the message_id
    temp_msg = await message.answer("Loading...")
    
    chat_id = message.chat.id
    msg_id = temp_msg.message_id
    game_id = f"{chat_id}_{msg_id}"
    
    create_session(game_id, question.id, is_nsfw=False)
    
    text = format_question_text(question)
    keyboard = get_voting_keyboard(game_id)
    
    await temp_msg.edit_text(text, reply_markup=keyboard)
