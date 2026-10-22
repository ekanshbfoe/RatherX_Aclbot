import time
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.questions import get_random_question
from database.categories import NSFW_CATEGORY
from services.game_session import create_session
from utils.formatting import format_question_text

router = Router()

_next_cooldowns: dict[int, float] = {}
NEXT_COOLDOWN_SECONDS = 10

# Game modes used in vote callback data: "sfw" = random from all SFW categories,
# otherwise a category key (the "nsfw" category doubles as the /nsfw mode)
RANDOM_MODE = "sfw"

def check_cooldown(chat_id: int) -> int:
    """Returns seconds left on this chat's cooldown, or 0 (and starts a new cooldown)."""
    now = time.time()

    # Rate limit: one new game per 10 seconds per chat
    last = _next_cooldowns.get(chat_id, 0)
    if now - last < NEXT_COOLDOWN_SECONDS:
        return max(1, int(NEXT_COOLDOWN_SECONDS - (now - last)))

    _next_cooldowns[chat_id] = now
    return 0

async def send_question(message: types.Message, mode: str = RANDOM_MODE):
    """Posts a new question for the given mode as a reply and starts its game session."""
    if mode == RANDOM_MODE:
        question = get_random_question(nsfw=False)
    else:
        question = get_random_question(category=mode)

    if not question:
        await message.reply("No questions found in the database!")
        return

    is_nsfw = (mode == NSFW_CATEGORY)

    # Build initial buttons
    builder = InlineKeyboardBuilder()
    builder.button(text="🔵", callback_data=f"vote:{mode}:{question.id}:a")
    builder.button(text="🔴", callback_data=f"vote:{mode}:{question.id}:b")
    builder.adjust(2)

    text = format_question_text(
        question.option_blue,
        question.option_red,
        is_nsfw=is_nsfw
    )

    msg = await message.reply(text, reply_markup=builder.as_markup(), parse_mode="HTML")

    game_id = f"{message.chat.id}:{msg.message_id}"
    create_session(game_id, question.id, is_nsfw=is_nsfw)

@router.message(Command("next"))
async def cmd_next(message: types.Message):
    remaining = check_cooldown(message.chat.id)
    if remaining:
        await message.reply(f"⏳ Please wait {remaining}s before starting a new game.")
        return

    await send_question(message, RANDOM_MODE)
