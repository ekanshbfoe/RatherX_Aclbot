from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("feedback"))
async def cmd_feedback(message: Message):
    await message.answer("Thank you for your feedback! We will review it shortly.")
