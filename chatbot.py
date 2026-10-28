"""
File:    chatbot.py
Purpose: Finds the best matching intent for a user's grammar question
         and returns a reply from the knowledge base (data/intents.json).
Author:  Muneeb (Roll No. 073)
Date:    27 October 2026
"""

import json
import random
import re
from difflib import SequenceMatcher
from pathlib import Path

# Folder where this file is saved. Used to build file paths that work from anywhere.
BASE_FOLDER = Path(__file__).parent
INTENTS_FILE = BASE_FOLDER / "data" / "intents.json"

# Minimum similarity (0 to 1) needed to accept a match. Below this we use the fallback.
MATCH_THRESHOLD = 0.6

FALLBACK_REPLY = ("I am sorry, I did not understand that. Could you rephrase your question? "
                  "You can try one of the sample questions in the sidebar.")


def load_intents():
    """
    Read the knowledge base from the JSON file.
    Input:  nothing
    Output: a list of intents (each intent is a dictionary with tag, patterns, responses)
    """
    with open(INTENTS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data["intents"]


def clean_text(text):
    """
    Make text simple so different ways of writing match each other.
    Input:  any string, e.g. "What is a NOUN??"
    Output: cleaned string, e.g. "what is a noun"
    """
    text = text.lower()                        # "NOUN" and "noun" become the same
    text = re.sub(r"[^a-z0-9\s]", " ", text)   # remove punctuation like ? ! , . '
    text = re.sub(r"\s+", " ", text)           # turn many spaces into one space
    return text.strip()                        # remove spaces at start and end


def get_similarity(text1, text2):
    """
    Compare two strings and tell how similar they are.
    Input:  two strings
    Output: a number between 0 (totally different) and 1 (exactly the same)
    This is what lets the bot tolerate small spelling mistakes like 'pronoun' vs 'pronon'.
    """
    return SequenceMatcher(None, text1, text2).ratio()


def find_best_intent(user_message, intents):
    """
    Compare the user's message with every pattern and keep the best one.
    Input:  user_message (string), intents (list from load_intents)
    Output: (best_intent, best_score) -> best_intent is a dictionary or None
    """
    cleaned_message = clean_text(user_message)
    best_intent = None
    best_score = 0.0

    for intent in intents:
        for pattern in intent["patterns"]:
            score = get_similarity(cleaned_message, clean_text(pattern))
            if score > best_score:          # found a better match, remember it
                best_score = score
                best_intent = intent

    return best_intent, best_score


def get_response(user_message, intents):
    """
    Main function of this file: decide the chatbot's reply.
    Input:  user_message (string), intents (list)
    Output: (reply_text, intent_tag, confidence_score)
    """
    best_intent, best_score = find_best_intent(user_message, intents)

    # If nothing is similar enough, give the polite fallback reply.
    if best_intent is None or best_score < MATCH_THRESHOLD:
        return FALLBACK_REPLY, "unknown", best_score

    # Pick one of the possible responses randomly so the bot feels less robotic.
    reply = random.choice(best_intent["responses"])
    return reply, best_intent["tag"], best_score
