from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.categories import CATEGORIES
from handlers.commands.next import check_cooldown, send_question

router = Router()

_CATEGORY_KEYS = {key for key, _, _ in CATEGORIES}

@router.message(Command("categories"))
async def cmd_categories(message: types.Message):
    builder = InlineKeyboardBuilder()
    for key, emoji, label in CATEGORIES:
        builder.button(text=f"{emoji} {label}", callback_data=f"cat:{key}")
    builder.adjust(3)

    await message.reply("🎯 <b>Pick a category:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(lambda c: c.data and c.data.startswith('cat:'))
async def process_category(callback_query: types.CallbackQuery):
    category = callback_query.data.split(':', 1)[1]
    if category not in _CATEGORY_KEYS:
        await callback_query.answer("Unknown category.", show_alert=True)
        return

    remaining = check_cooldown(callback_query.message.chat.id)
    if remaining:
        await callback_query.answer(f"⏳ Please wait {remaining}s before starting a new game.", show_alert=True)
        return

    await callback_query.answer()
    await send_question(callback_query.message, category)
