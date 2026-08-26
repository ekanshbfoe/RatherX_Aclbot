import html
import re
from aiogram.exceptions import TelegramBadRequest
import logging

log = logging.getLogger(__name__)

def create_progress_bar(percentage: float, length: int = 10) -> str:
    """Creates a simple block progress bar."""
    filled_blocks = int(round((percentage / 100) * length))
    empty_blocks = length - filled_blocks
    return "█" * filled_blocks + "░" * empty_blocks

def format_question_text(option_a: str, option_b: str, 
                         votes_a: int = 0, votes_b: int = 0, 
                         show_stats: bool = False, 
                         players_a: list = None, players_b: list = None, 
                         waiting_text: str = "",
                         is_nsfw: bool = False) -> str:
    """Formats the question message text."""
    # Ensure lists are instantiated
    if players_a is None: players_a = []
    if players_b is None: players_b = []
    
    option_a = html.escape(option_a)
    option_b = html.escape(option_b)
    
    text = "<b>[18+] Would you rather...</b>\n\n" if is_nsfw else "<b>Would you rather...</b>\n\n"
    
    if show_stats:
        total_votes = votes_a + votes_b
        pct_a = (votes_a / total_votes * 100) if total_votes > 0 else 0
        pct_b = (votes_b / total_votes * 100) if total_votes > 0 else 0
        
        text += f"<b>({int(round(pct_a))}%)</b> 🔵 {option_a}\n"
        text += f"<b>({int(round(pct_b))}%)</b> 🔴 {option_b}\n\n"
        
        if players_a:
            text += f"🔵 {', '.join([html.escape(p) for p in players_a])}\n"
        if players_b:
            text += f"🔴 {', '.join([html.escape(p) for p in players_b])}\n"
    else:
        text += f"🔵 {option_a}\n"
        text += f"🔴 {option_b}\n\n"
        
    if waiting_text:
        text += f"<i>{waiting_text}</i>"
    elif not show_stats:
        text += "Select your answer:"
        
    return text

async def safe_edit_message_text(message, text: str, reply_markup=None):
    """Edits message text and gracefully ignores MessageNotModified errors."""
    try:
        if reply_markup is not None:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await message.edit_text(text, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass # Ignore benign error
        else:
            log.error(f"Error editing message: {e}")
            raise e

def generate_ship_name(name1: str, name2: str) -> str:
    # Strip non-alphanumeric chars for a clean hashtag
    c1 = re.sub(r'\W+', '', name1)
    c2 = re.sub(r'\W+', '', name2)
    if not c1: c1 = "User"
    if not c2: c2 = "User"
    
    part1 = c1[:len(c1)//2 + (1 if len(c1)%2 != 0 else 0)]
    part2 = c2[len(c2)//2:]
    return f"#{part1}{part2}"

def generate_progress_bar(percentage: float) -> str:
    filled = int(round(percentage / 10))
    if filled > 10: filled = 10
    if filled < 0: filled = 0
    empty = 10 - filled
    return "█" * filled + "░" * empty

def format_interactive_couple_board(couples: list, scope_name: str) -> str:
    """Formats the top 10 interactive couple board UI."""
    text = f"<b>📊 COUPLE BOARD: [{scope_name}] 📊</b>\n\n"
    
    if not couples:
        return text + "<i>⚠️ No couples have answered 5+ common questions in this sector yet! Play more rounds to unlock the board.</i>"
        
    for i, c in enumerate(couples[:10]):
        rank = i + 1
        ship = generate_ship_name(c['u1_name'], c['u2_name'])
        prog = generate_progress_bar(c['percentage'])
        
        text += f"<b>#{rank} {ship} 📈</b>\n"
        text += f"{html.escape(c['u1_name'])} x {html.escape(c['u2_name'])}\n"
        text += f"{prog} {c['percentage']:.1f}% ({c['points']} pts)\n"
        if rank == 1:
            text += "<i>\"Built for each other!\"</i>\n"
        text += "\n"
    text += "<i>*Couples must share 5+ answers to unlock.*</i>"
    return text

def format_mylove_dm(matches: list, user_id: int) -> str:
    matches.sort(key=lambda x: (x["percentage"], x["common_count"], x["points"]), reverse=True)
    
    top = matches[0]
    top_name = top["u1_name"] if top["u2_id"] == user_id else top["u2_name"]
    
    text = f"<b>💖 Your Top Match Today in this group 💖</b>\n\n"
    text += f"Ooh, the chemistry between you and {html.escape(top_name)} is off the charts today at {top['percentage']:.1f}%! 👀\n\n"
    
    text += "<b>📊 Your Top 5 Matches:</b>\n"
    for i, c in enumerate(matches[:5]):
        name = c["u1_name"] if c["u2_id"] == user_id else c["u2_name"]
        text += f"{i+1}. {html.escape(name)} - {c['percentage']:.1f}%\n"
        
    return text

def format_compatibility(result: dict) -> str:
    text = "<b>⚡ COMPATIBILITY SCAN ⚡</b>\n\n"
    text += f"Target: {html.escape(result['u1_name'])} x {html.escape(result['u2_name'])}\n"
    text += f"Match: <b>{result['percentage']:.1f}%</b> ({result['points']} pts across {result['common_count']} questions)\n\n"
    
    pct = result['percentage']
    if pct >= 90:
        quote = "Soulmates! You two are literally perfect for each other."
    elif pct >= 75:
        quote = "Amazing match! The chemistry is undeniable."
    elif pct >= 50:
        quote = "Not bad! You have a solid foundational connection."
    elif pct >= 30:
        quote = "A bit rocky... but opposites attract, right?"
    else:
        quote = "Enemies! You two agree on absolutely nothing."
        
    text += f"<i>\"{quote}\"</i>"
    return text
