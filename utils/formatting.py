from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.questions import Question
from services.game_session import GameSession

def format_question_text(question: Question) -> str:
    prefix = "[18+] " if question.is_nsfw else ""
    return (
        f"{prefix}Would you rather...\n\n"
        f"🔵 {question.option_a}\n"
        f"🔴 {question.option_b}\n\n"
        f"Select your answer:"
    )

def format_waiting_text(question: Question, session: GameSession, chat_type: str = "group") -> str:
    prefix = "[18+] " if question.is_nsfw else ""
    names = ", ".join(session.voters_names.values())
    
    if chat_type == "private":
        waiting_msg = f"{names} already answered!"
    else:
        import time
        elapsed = time.time() - session.created_at
        remaining = max(1, 15 - int(elapsed))
        waiting_msg = f"Waiting {remaining} sec for players to answer...\n\n{names} already answered!"
        
    return (
        f"{prefix}Would you rather...\n\n"
        f"🔵 {question.option_a}\n"
        f"🔴 {question.option_b}\n\n"
        f"{waiting_msg}"
    )

def format_results_text(question: Question, session: GameSession) -> str:
    prefix = "[18+] " if question.is_nsfw else ""
    total_votes = len(session.votes_a) + len(session.votes_b)
    
    if total_votes == 0:
        pct_a = 0
        pct_b = 0
    else:
        pct_a = int((len(session.votes_a) / total_votes) * 100)
        pct_b = 100 - pct_a
        
    names_a = ", ".join([session.voters_names[uid] for uid in session.votes_a])
    names_b = ", ".join([session.voters_names[uid] for uid in session.votes_b])
    
    if not names_a: names_a = "None"
    if not names_b: names_b = "None"
    
    return (
        f"{prefix}Would you rather...\n\n"
        f"({pct_a}%) 🔵 {question.option_a}\n"
        f"({pct_b}%) 🔴 {question.option_b}\n\n"
        f"🔵 {names_a}\n"
        f"🔴 {names_b}"
    )

def get_voting_keyboard(game_id: str) -> InlineKeyboardMarkup:
    # We pass the game_id to the callback data
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔵", callback_data=f"vote_a_{game_id}"),
            InlineKeyboardButton(text="🔴", callback_data=f"vote_b_{game_id}")
        ]
    ])

def get_next_question_keyboard(is_nsfw: bool) -> InlineKeyboardMarkup:
    # "is_nsfw" passed as 1 or 0
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Next Question", callback_data=f"next_q_{int(is_nsfw)}")]
    ])
