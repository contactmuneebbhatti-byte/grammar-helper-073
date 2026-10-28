"""
File:    app.py
Purpose: Streamlit web interface for the English Grammar Helper chatbot.
         It has three modes: Ask a Grammar Question, Check My Sentence, Grammar Quiz.
         Run with:  streamlit run app.py
Author:  Muneeb (Roll No. 073)
Date:    27 October 2026
"""

import streamlit as st

from chatbot import load_intents, get_response, find_best_intent, MATCH_THRESHOLD
from grammar_checker import load_rules, build_check_reply
from quiz import (load_questions, pick_random_questions, format_question, check_answer,
                  get_correct_option_text, final_result_message)

# ---------------- Basic settings ----------------
STUDENT_NAME = "Muneeb"
ROLL_NUMBER = "073"
PROJECT_NAME = "English Grammar Helper Chatbot"

MODE_ASK = "💬 Ask a Grammar Question"
MODE_CHECK = "✍️ Check My Sentence"
MODE_QUIZ = "🧠 Grammar Quiz"

GREETING_MESSAGE = ("Assalam o Alaikum! 👋 I am your **English Grammar Helper**.\n\n"
                    "I can answer grammar questions, check your sentences like a mini Grammarly, "
                    "and test you with a quiz. Choose a mode from the sidebar to begin.")

# Instructions shown when the user switches to a mode
MODE_INSTRUCTIONS = {
    MODE_ASK: "You are in **Ask a Grammar Question** mode. Ask me anything, e.g. *What is present perfect tense?*",
    MODE_CHECK: "You are in **Check My Sentence** mode. Type any English sentence and I will check it for mistakes.",
    MODE_QUIZ: "You are in **Grammar Quiz** mode. Type **start** to begin a 10-question quiz.",
}

SAMPLE_QUESTIONS = {
    MODE_ASK: ["What is a noun?", "When do I use present perfect tense?",
               "Difference between since and for", "What is passive voice?", "a or an?"],
    MODE_CHECK: ["he go to school every day", "She have a apple",
                 "i recieve the the letter tommorow", "We was going to the libary"],
    MODE_QUIZ: ["start", "B", "stop"],
}

st.set_page_config(page_title="English Grammar Helper", page_icon="📝")


# ---------------- Load knowledge base once ----------------
@st.cache_data
def load_all_data():
    """
    Load intents, grammar rules and quiz questions from the data folder.
    st.cache_data makes Streamlit load the files only once, not on every click.
    Output: (intents, rules, questions)
    """
    return load_intents(), load_rules(), load_questions()


INTENTS, RULES, QUESTIONS = load_all_data()


# ---------------- Session state (memory of the chat) ----------------
def start_new_chat():
    """
    Reset the chat history and quiz progress to the starting values.
    """
    st.session_state.messages = [{"role": "assistant", "content": GREETING_MESSAGE}]
    st.session_state.quiz_active = False
    st.session_state.quiz_questions = []
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0


# Streamlit runs this file again on every action, so we only create the memory once.
if "messages" not in st.session_state:
    start_new_chat()


def add_message(role, content, info=None):
    """
    Save one message in the chat history.
    Input: role ('user' or 'assistant'), content (text), info (small grey caption, optional)
    """
    st.session_state.messages.append({"role": role, "content": content, "info": info})


def on_mode_change():
    """
    Called automatically when the user picks a different mode in the sidebar.
    It stops any running quiz and tells the user how the new mode works.
    """
    st.session_state.quiz_active = False
    add_message("assistant", MODE_INSTRUCTIONS[st.session_state.mode])


# ---------------- Quiz logic ----------------
def handle_quiz(user_text):
    """
    Handle a message while in quiz mode.
    Input:  user_text (string)
    Output: (reply, info)
    """
    answer = user_text.strip().lower()

    # Quiz not started yet
    if not st.session_state.quiz_active:
        if answer in ["start", "start quiz", "yes", "begin", "play again"]:
            st.session_state.quiz_questions = pick_random_questions(QUESTIONS)
            st.session_state.quiz_index = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_active = True
            first_question = st.session_state.quiz_questions[0]
            total = len(st.session_state.quiz_questions)
            return "Let's begin! 🎯\n\n" + format_question(first_question, 1, total), None
        return "Type **start** to begin the quiz.", None

    # User wants to stop in the middle
    if answer in ["stop", "quit", "exit", "end"]:
        st.session_state.quiz_active = False
        return final_result_message(st.session_state.quiz_score, st.session_state.quiz_index), None

    # Answer must be a, b, c or d
    if answer not in ["a", "b", "c", "d"]:
        return "Please answer with **A**, **B**, **C** or **D** (or type **stop**).", None

    questions = st.session_state.quiz_questions
    current_question = questions[st.session_state.quiz_index]

    if check_answer(answer, current_question):
        st.session_state.quiz_score += 1
        feedback = "✅ **Correct!** " + current_question["explanation"]
    else:
        feedback = (f"❌ **Wrong.** The correct answer is **{get_correct_option_text(current_question)}**.\n\n"
                    f"{current_question['explanation']}")

    st.session_state.quiz_index += 1
    number_done = st.session_state.quiz_index
    score_info = f"Score so far: {st.session_state.quiz_score}/{number_done}"

    # More questions left -> show the next one
    if number_done < len(questions):
        next_question = questions[number_done]
        reply = feedback + "\n\n---\n\n" + format_question(next_question, number_done + 1, len(questions))
        return reply, score_info

    # No questions left -> show the final result
    st.session_state.quiz_active = False
    return feedback + "\n\n---\n\n" + final_result_message(st.session_state.quiz_score, len(questions)), None


# ---------------- Main reply function ----------------
def get_bot_reply(user_text):
    """
    Decide the bot's reply depending on the selected mode.
    Input:  user_text (string)
    Output: (reply_text, info_caption)
    """
    text = user_text.strip()

    # Empty message or only numbers -> ask for a proper sentence
    if text == "":
        return "Please type a message so I can help you.", None
    if text.replace(" ", "").isdigit():
        return "I can only understand words, not just numbers. Please type a sentence or a grammar question.", None

    mode = st.session_state.mode

    if mode == MODE_QUIZ and st.session_state.quiz_active:
        return handle_quiz(text)

    # Greetings and farewells work in every mode
    intent, score = find_best_intent(text, INTENTS)
    is_small_talk = intent is not None and intent["tag"] in ["greeting", "farewell"]
    if is_small_talk and score >= MATCH_THRESHOLD:
        reply, tag, score = get_response(text, INTENTS)
        return reply, f"Intent: {tag} · Confidence: {score:.0%}"

    if mode == MODE_QUIZ:
        return handle_quiz(text)

    if mode == MODE_CHECK:
        reply, mistake_count = build_check_reply(text, RULES)
        return reply, f"Mode: sentence check · Mistakes found: {mistake_count}"

    # MODE_ASK
    reply, tag, score = get_response(text, INTENTS)
    return reply, f"Intent: {tag} · Confidence: {score:.0%}"


def chat_as_text():
    """
    Convert the whole chat into plain text for the download button.
    Output: a string with every message on its own lines
    """
    lines = [f"{PROJECT_NAME} - {STUDENT_NAME} ({ROLL_NUMBER})", "=" * 50, ""]
    for message in st.session_state.messages:
        speaker = "You" if message["role"] == "user" else "Bot"
        lines.append(f"{speaker}: {message['content']}")
        lines.append("")
    return "\n".join(lines)


# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("📝 About")
    st.write("A chatbot that helps students learn English grammar. "
             "It answers grammar questions, checks sentences for common mistakes "
             "and tests you with a quiz.")

    st.radio("Choose a mode:", [MODE_ASK, MODE_CHECK, MODE_QUIZ], key="mode", on_change=on_mode_change)

    st.subheader("Try these:")
    for sample in SAMPLE_QUESTIONS[st.session_state.mode]:
        st.markdown(f"- {sample}")

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        start_new_chat()
        st.rerun()

    st.download_button("⬇️ Download Chat", data=chat_as_text(),
                       file_name="grammar_chat.txt", mime="text/plain", use_container_width=True)


# ---------------- Main page ----------------
st.title("📝 English Grammar Helper")
st.caption(f"**Project:** {PROJECT_NAME}  |  **Student:** {STUDENT_NAME}  |  **Roll No:** {ROLL_NUMBER}")

# Show all old messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("info"):
            st.caption(message["info"])

# Wait for new input
user_input = st.chat_input("Type your message here...")

if user_input is not None:
    add_message("user", user_input)
    bot_reply, bot_info = get_bot_reply(user_input)
    add_message("assistant", bot_reply, bot_info)
    st.rerun()      # refresh the page so the new messages appear
