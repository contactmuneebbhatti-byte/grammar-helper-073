"""
File:    quiz.py
Purpose: Loads grammar MCQs from data/quiz.json, picks random questions,
         formats them for the chat and checks the user's answers.
Author:  Muneeb (Roll No. 073)
Date:    27 October 2026
"""

import json
import random
from pathlib import Path

BASE_FOLDER = Path(__file__).parent
QUIZ_FILE = BASE_FOLDER / "data" / "quiz.json"

QUESTIONS_PER_QUIZ = 10
OPTION_LETTERS = ["A", "B", "C", "D"]


def load_questions():
    """
    Read all quiz questions from the JSON file.
    Output: list of questions (each has question, options, answer, explanation)
    """
    with open(QUIZ_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data["questions"]


def pick_random_questions(all_questions, count=QUESTIONS_PER_QUIZ):
    """
    Choose some questions randomly so every quiz is different.
    Input:  all_questions (list), count (how many to pick)
    Output: a new shuffled list of questions
    """
    count = min(count, len(all_questions))      # cannot pick more than we have
    return random.sample(all_questions, count)


def format_question(question, number, total):
    """
    Make a question look nice in the chat.
    Input:  question (dictionary), number (1, 2, 3...), total questions
    Output: text like 'Question 1 of 10 ... A) go  B) goes ...'
    """
    text = f"**Question {number} of {total}**\n\n{question['question']}\n\n"
    for letter, option in zip(OPTION_LETTERS, question["options"]):
        text += f"- **{letter})** {option}\n"
    text += "\nType **A**, **B**, **C** or **D**  (or **stop** to end the quiz)."
    return text


def check_answer(user_answer, question):
    """
    Check whether the user's answer is correct.
    Input:  user_answer like 'b' or 'B', question (dictionary)
    Output: True if correct, otherwise False
    """
    return user_answer.strip().upper() == question["answer"]


def get_correct_option_text(question):
    """
    Return the correct answer with its letter, e.g. 'B) goes'.
    """
    index = OPTION_LETTERS.index(question["answer"])   # 'B' -> 1
    return f"{question['answer']}) {question['options'][index]}"


def final_result_message(score, total):
    """
    Build the message shown when the quiz ends.
    Input:  score (correct answers), total (questions asked)
    Output: text with score, percentage and a short comment
    """
    if total == 0:
        return "Quiz ended. You did not answer any question."

    percentage = round(score / total * 100)

    if percentage >= 80:
        comment = "Excellent! Your grammar is very strong. 🌟"
    elif percentage >= 50:
        comment = "Good effort! Revise the topics you missed. 👍"
    else:
        comment = "Keep practising. Ask me about the topics you got wrong. 💪"

    return (f"🏁 **Quiz finished!**\n\nYour score: **{score} / {total}** ({percentage}%)\n\n"
            f"{comment}\n\nType **start** to play again.")
