from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from handlers.commands.start import WELCOME_TEXT

router = Router()

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(WELCOME_TEXT)
