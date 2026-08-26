from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.reply(
        "🆘 **How to play:**\n\n"
        "• **/next** - Play a standard SFW question.\n"
        "• **/nsfw** - Play a spicy NSFW question.\n"
        "• **Inline Mode:** Type my username in any chat to send a challenge to your friends!\n\n"
        "In groups, the first vote starts a 15-second timer. Be quick!"
    )
