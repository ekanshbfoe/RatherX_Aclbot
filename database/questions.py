import random
from dataclasses import dataclass
from typing import List

@dataclass
class Question:
    id: str
    option_a: str
    option_b: str
    is_nsfw: bool = False

# Mock Database
SFW_QUESTIONS = [
    Question("sfw_1", "Everything taste too spicy", "Everything taste too sweet"),
    Question("sfw_2", "Always be 10 minutes late", "Always be 20 minutes early"),
    Question("sfw_3", "Have the ability to fly", "Have the ability to become invisible"),
    Question("sfw_4", "Lose all your money and valuables", "Lose all the pictures you have ever taken"),
    Question("sfw_5", "Only be able to whisper", "Only be able to shout"),
]

NSFW_QUESTIONS = [
    Question("nsfw_1", "Have sex without kissing your partner", "Have sex without using your hands at all", is_nsfw=True),
    Question("nsfw_2", "Send a nude to your boss by accident", "Send a nude to your parents by accident", is_nsfw=True),
    Question("nsfw_3", "Give up sex for a year", "Give up your favorite food for a year", is_nsfw=True),
    Question("nsfw_4", "Walk in on your parents having sex", "Have your parents walk in on you having sex", is_nsfw=True),
]

def get_random_question(nsfw: bool = False) -> Question:
    if nsfw:
        return random.choice(NSFW_QUESTIONS)
    return random.choice(SFW_QUESTIONS)

def get_question_by_id(question_id: str) -> Question:
    for q in SFW_QUESTIONS + NSFW_QUESTIONS:
        if q.id == question_id:
            return q
    return SFW_QUESTIONS[0]
