import asyncio
import time
import logging
import itertools
from database.questions import get_question_by_id
from dataclasses import dataclass, field
from typing import Set, Dict, Optional

log = logging.getLogger(__name__)

@dataclass
class GameSession:
    question_id: str
    is_nsfw: bool
    created_at: float = field(default_factory=time.time)
    votes_a: Set[int] = field(default_factory=set) # User IDs for option blue
    votes_b: Set[int] = field(default_factory=set) # User IDs for option red
    voters_names: Dict[int, str] = field(default_factory=dict) # User ID -> first name
    timer_task: Optional[asyncio.Task] = None
    is_finished: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    last_ui_update_time: float = 0.0

# In-memory storage for active games
# Key: f"{chat_id}_{message_id}" for groups/private or f"inline_{inline_message_id}" for inline mode
active_games: Dict[str, GameSession] = {}

def get_session(game_id: str) -> Optional[GameSession]:
    return active_games.get(game_id)

def create_session(game_id: str, question_id: str, is_nsfw: bool) -> GameSession:
    session = GameSession(question_id=question_id, is_nsfw=is_nsfw)
    active_games[game_id] = session
    return session

def remove_session(game_id: str):
    session = active_games.pop(game_id, None)
    if session and session.timer_task and not session.timer_task.done():
        session.timer_task.cancel()
    log.debug(f"Removed session {game_id}")

async def cleanup_stale_sessions(max_age_seconds: int = 1800):
    """
    Periodic task to aggressively remove stale sessions older than 30 minutes.
    (Normal sessions resolve themselves in 15s and pop(), this is a fallback).
    """
    while True:
        await asyncio.sleep(60) # Check every minute
        now = time.time()
        stale_keys = [
            game_id for game_id, session in active_games.items()
            if now - session.created_at > max_age_seconds
        ]
        for game_id in stale_keys:
            remove_session(game_id)

# ----------------- GLOBAL & LOCAL HISTORY & MATCHING -----------------

# global_history: Dict[user_id, {"name": str, "username": str, "votes": {question_id: str}}]
global_history: Dict[int, dict] = {}
# local_history: Dict[chat_instance, Dict[user_id, {"name": str, "username": str, "votes": {question_id: str}}]]
local_history: Dict[str, Dict[int, dict]] = {}
# chat_id_to_instance: Maps standard group chat_id to the hidden chat_instance
chat_id_to_instance: Dict[int, str] = {}

def record_user_vote(user_id: int, user_name: str, question_id: str, vote_choice: str, chat_instance: Optional[str] = None, username: Optional[str] = None):
    # Global Tracking
    if user_id not in global_history:
        global_history[user_id] = {"name": user_name, "username": username, "votes": {}}
        
    global_history[user_id]["name"] = user_name
    if username:
        global_history[user_id]["username"] = username
    global_history[user_id]["votes"][question_id] = vote_choice
    
    # Local Tracking
    if chat_instance is not None:
        if chat_instance not in local_history:
            local_history[chat_instance] = {}
        if user_id not in local_history[chat_instance]:
            local_history[chat_instance][user_id] = {"name": user_name, "username": username, "votes": {}}
        local_history[chat_instance][user_id]["name"] = user_name
        if username:
            local_history[chat_instance][user_id]["username"] = username
        local_history[chat_instance][user_id]["votes"][question_id] = vote_choice

def calculate_couples(scope: str, identifier = None) -> list:
    if scope == "local":
        if identifier not in local_history:
            return []
        users_dict = local_history[identifier]
        user_ids = list(users_dict.keys())
        pairs = itertools.combinations(user_ids, 2)
    elif scope == "personal":
        users_dict = global_history
        user_ids = list(users_dict.keys())
        if identifier not in user_ids:
            return []
        other_users = [u for u in user_ids if u != identifier]
        pairs = [(identifier, other) for other in other_users]
    else: # global
        users_dict = global_history
        user_ids = list(users_dict.keys())
        pairs = itertools.combinations(user_ids, 2)
    
    couples = []
    
    for uid1, uid2 in pairs:
        u1_data = users_dict[uid1]
        u2_data = users_dict[uid2]
        
        u1_votes = u1_data["votes"]
        u2_votes = u2_data["votes"]
        
        common_qids = set(u1_votes.keys()) & set(u2_votes.keys())
        if len(common_qids) < 5:
            continue
            
        earned_points = 0
        possible_points = 0
        
        for qid in common_qids:
            v1 = u1_votes[qid]
            v2 = u2_votes[qid]
            
            question = get_question_by_id(qid)
            if not question:
                continue
                
            if v1 != v2:
                # Scenario C (Disagreement)
                possible_points += 1
            else:
                # Determine global majority
                majority_option = 'a' if question.global_votes_blue > question.global_votes_red else 'b'
                
                if v1 == majority_option:
                    # Scenario A (Popular Agreement)
                    earned_points += 1
                    possible_points += 1
                else:
                    # Scenario B (Rare/Weird Agreement)
                    earned_points += 2
                    possible_points += 2
                
        percentage = (earned_points / possible_points) * 100 if possible_points > 0 else 0
        
        couples.append({
            "u1_id": uid1,
            "u2_id": uid2,
            "u1_name": u1_data["name"],
            "u2_name": u2_data["name"],
            "percentage": round(percentage, 1),
            "points": earned_points,
            "common_count": len(common_qids)
        })
        
    # Sort by percentage desc, common count desc, points desc
    couples.sort(key=lambda x: (x["percentage"], x["common_count"], x["points"]), reverse=True)
    return couples

def calculate_specific_compatibility(users_dict: dict, uid1: int, uid2: int) -> Optional[dict]:
    """Calculates the specific compatibility between two users in a given dictionary."""
    if uid1 not in users_dict or uid2 not in users_dict:
        return None
        
    u1_data = users_dict[uid1]
    u2_data = users_dict[uid2]
    
    u1_votes = u1_data["votes"]
    u2_votes = u2_data["votes"]
    
    common_qids = set(u1_votes.keys()) & set(u2_votes.keys())
    if len(common_qids) < 5:
        return None
        
    earned_points = 0
    possible_points = 0
    
    for qid in common_qids:
        v1 = u1_votes[qid]
        v2 = u2_votes[qid]
        
        question = get_question_by_id(qid)
        if not question:
            continue
            
        if v1 != v2:
            possible_points += 1
        else:
            majority_option = 'a' if question.global_votes_blue > question.global_votes_red else 'b'
            if v1 == majority_option:
                earned_points += 1
                possible_points += 1
            else:
                earned_points += 2
                possible_points += 2
                
    percentage = (earned_points / possible_points) * 100 if possible_points > 0 else 0
    
    return {
        "u1_name": u1_data["name"],
        "u2_name": u2_data["name"],
        "percentage": round(percentage, 1),
        "points": earned_points,
        "common_count": len(common_qids)
    }
