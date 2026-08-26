from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1] == "love":
        await message.reply("💖 Successfully connected to your DMs! You can now use the /mylove command in group chats to receive your secret stats.")
        return

    await message.reply(
        "👋 Welcome to Would You Rather!\n\n"
        "Send /next for a standard question or /nsfw for a spicy one!\n\n"
        "You can also add me to a group and play with friends, or use inline mode "
        "by typing `@YourBotUsername` in any chat!"
    )
