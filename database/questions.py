import orjson
import random
import os
import glob
import logging
from dataclasses import dataclass
from database.categories import NSFW_CATEGORY

log = logging.getLogger(__name__)

@dataclass
class Question:
    id: str
    question: str
    option_blue: str
    option_red: str
    global_votes_blue: int
    global_votes_red: int
    category: str

    @property
    def is_nsfw(self) -> bool:
        return self.category == NSFW_CATEGORY

# In-memory storage for questions
QUESTIONS_BY_CATEGORY: dict[str, list[Question]] = {}
SFW_QUESTIONS: list[Question] = []  # All non-NSFW categories combined (used by /next)
ALL_QUESTIONS_MAP: dict[str, Question] = {}

def load_questions():
    """Load every data/questions_<category>.json file into memory at startup."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern = os.path.join(base_dir, "data", "questions_*.json")

    QUESTIONS_BY_CATEGORY.clear()
    SFW_QUESTIONS.clear()
    ALL_QUESTIONS_MAP.clear()

    for filepath in sorted(glob.glob(pattern)):
        category = os.path.basename(filepath)[len("questions_"):-len(".json")]
        _load_file(filepath, category)

    for category, questions in QUESTIONS_BY_CATEGORY.items():
        if category != NSFW_CATEGORY:
            SFW_QUESTIONS.extend(questions)

    log.info(f"Loaded {len(ALL_QUESTIONS_MAP)} questions across {len(QUESTIONS_BY_CATEGORY)} categories.")

def _load_file(filepath: str, category: str):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = orjson.loads(f.read())
        questions = QUESTIONS_BY_CATEGORY.setdefault(category, [])
        for item in data:
            q = Question(
                id=item.get("id"),
                question=item.get("question"),
                option_blue=item.get("option_blue"),
                option_red=item.get("option_red"),
                global_votes_blue=item.get("global_votes_blue", 0),
                global_votes_red=item.get("global_votes_red", 0),
                category=category
            )
            questions.append(q)
            ALL_QUESTIONS_MAP[q.id] = q
    except Exception as e:
        log.error(f"Error loading {filepath}: {e}")

def get_random_question(nsfw: bool = False, exclude_id: str = None, category: str = None) -> Question:
    """Picks a random question from a category, the NSFW set, or all SFW categories."""
    if category:
        source_list = QUESTIONS_BY_CATEGORY.get(category, [])
    elif nsfw:
        source_list = QUESTIONS_BY_CATEGORY.get(NSFW_CATEGORY, [])
    else:
        source_list = SFW_QUESTIONS

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
