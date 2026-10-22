from aiogram import Router, types
from aiogram.filters import Command
from database.categories import NSFW_CATEGORY
from handlers.commands.next import check_cooldown, send_question

router = Router()

@router.message(Command("nsfw"))
async def cmd_nsfw(message: types.Message):
    remaining = check_cooldown(message.chat.id)
    if remaining:
        await message.reply(f"⏳ Please wait {remaining}s before starting a new game.")
        return

    await send_question(message, NSFW_CATEGORY)
