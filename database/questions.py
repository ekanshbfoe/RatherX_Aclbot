import orjson
import random
import os
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

@dataclass
class Question:
    id: str
    question: str
    option_blue: str
    option_red: str
    global_votes_blue: int
    global_votes_red: int
    is_nsfw: bool = False

# In-memory storage for questions
SFW_QUESTIONS = []
NSFW_QUESTIONS = []
ALL_QUESTIONS_MAP = {}

def load_questions():
    """Load JSON files into memory at startup."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sfw_path = os.path.join(base_dir, "data", "questions_sfw.json")
    nsfw_path = os.path.join(base_dir, "data", "questions_nsfw.json")
    
    global SFW_QUESTIONS, NSFW_QUESTIONS, ALL_QUESTIONS_MAP
    SFW_QUESTIONS.clear()
    NSFW_QUESTIONS.clear()
    ALL_QUESTIONS_MAP.clear()
    
    _load_file(sfw_path, False)
    _load_file(nsfw_path, True)
    
    log.info(f"Loaded {len(SFW_QUESTIONS)} SFW questions and {len(NSFW_QUESTIONS)} NSFW questions.")

def _load_file(filepath: str, is_nsfw: bool):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = orjson.loads(f.read())
            for item in data:
                q = Question(
                    id=item.get("id"),
                    question=item.get("question"),
                    option_blue=item.get("option_blue"),
                    option_red=item.get("option_red"),
                    global_votes_blue=item.get("global_votes_blue", 0),
                    global_votes_red=item.get("global_votes_red", 0),
                    is_nsfw=is_nsfw
                )
                if is_nsfw:
                    NSFW_QUESTIONS.append(q)
                else:
                    SFW_QUESTIONS.append(q)
                ALL_QUESTIONS_MAP[q.id] = q
    except FileNotFoundError:
        log.warning(f"File not found: {filepath}. Starting with empty {'NSFW' if is_nsfw else 'SFW'} database.")
    except Exception as e:
        log.error(f"Error loading {filepath}: {e}")

def get_random_question(nsfw: bool = False, exclude_id: str = None) -> Question:
    source_list = NSFW_QUESTIONS if nsfw else SFW_QUESTIONS
    if not source_list:
        return None # Return None if no questions are available

    # Basic logic to prevent exact back-to-back repeats if possible
    if len(source_list) > 1 and exclude_id:
        filtered_list = [q for q in source_list if q.id != exclude_id]
        if filtered_list:
            return random.choice(filtered_list)
            
    return random.choice(source_list)

def get_question_by_id(question_id: str) -> Question:
    return ALL_QUESTIONS_MAP.get(question_id)
