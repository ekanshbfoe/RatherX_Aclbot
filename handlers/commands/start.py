from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.reply(
        "👋 Welcome to Would You Rather!\n\n"
        "Send /next for a standard question or /nsfw for a spicy one!\n\n"
        "You can also add me to a group and play with friends, or use inline mode "
        "by typing `@YourBotUsername` in any chat!"
    )
