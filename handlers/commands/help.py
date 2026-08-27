from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("help", prefix="/."))
async def cmd_help(message: types.Message):
    text = (
        "<b>『 RatherX Game Panel 👑 』</b>\n\n"
        "<b>🎮 Play the Game</b>\n"
        "• <code>/next</code> - Get a standard question.\n"
        "• <code>/nsfw</code> - Get an 18+ question.\n\n"
        "<b>💞 Social & Matchmaking</b>\n"
        "• <code>/xcouple</code> - View the Couple Board.\n"
        "• <code>/mylove</code> - Get your secret stats via DM.\n"
        "• <code>/compatibility @user1 @user2</code> - Scan a specific pair.\n\n"
        "<b>🛠️ Utility</b>\n"
        "• <code>/help</code> or <code>.help</code> - Show this menu.\n"
        "• <code>/feedback</code> or <code>.feedback</code> - Report a bug or request a feature."
    )
    await message.reply(text, parse_mode="HTML")
