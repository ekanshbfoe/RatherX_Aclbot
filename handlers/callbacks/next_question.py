from aiogram import Router, types
from handlers.commands.next import cmd_next
from handlers.commands.nsfw import cmd_nsfw
from aiogram.exceptions import TelegramBadRequest

router = Router()

@router.callback_query(lambda c: c.data in ["next_sfw", "next_nsfw"])
async def process_next_question(callback_query: types.CallbackQuery):
    await callback_query.answer()
    
    # Remove the 'Next Question' button from the previous message
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
        
    # Send a new question by mimicking the command
    if callback_query.data == "next_sfw":
        await cmd_next(callback_query.message)
    else:
        await cmd_nsfw(callback_query.message)
