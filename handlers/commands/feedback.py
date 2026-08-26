from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("feedback"))
async def cmd_feedback(message: types.Message):
    await message.reply(
        "Got an idea for a new question or found a bug? Let us know!"
    )
