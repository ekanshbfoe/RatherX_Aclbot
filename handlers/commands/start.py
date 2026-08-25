from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

WELCOME_TEXT = """Welcome to Would You Rather Bot!

🕹 How to play single player?
Use the following commands:
/next - get a new Would You Rather question
/nsfw - get a new NSFW (18+) question

👨‍👩‍👧‍👦 How to play in a group?
Add @RatherGameBot to your group and then use these commands:
/next@RatherGameBot - get a new Would You Rather question
/nsfw@RatherGameBot - get a new NSFW (18+) question

👫 How to play inline?
Type @RatherGameBot in a chat and select a question to play against a friend.

❓ Feedback or suggestions?
Please let us know with /feedback!

To view this info again, use /help."""

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(WELCOME_TEXT)
