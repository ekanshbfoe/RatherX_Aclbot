from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(Command("xcouple"))
async def cmd_xcouple(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📍 Current Chat", callback_data="xboard:local")
    builder.button(text="🌍 Global Server", callback_data="xboard:global")
    builder.button(text="👤 My Matches", callback_data="xboard:personal")
    builder.adjust(1)
    
    await message.reply("📊 <b>Matchmaking Database Accessed.</b>\nSelect a sector to scan:", reply_markup=builder.as_markup(), parse_mode="HTML")
