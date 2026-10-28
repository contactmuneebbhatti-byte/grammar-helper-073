"""
File:    grammar_checker.py
Purpose: Checks an English sentence for common mistakes (spelling, a/an,
         he/she/it + verb, wrong phrases, capital letters, full stop)
         and returns the corrected sentence with explanations.
         All rules are stored in data/grammar_rules.json.
Author:  Muneeb (Roll No. 073)
Date:    27 October 2026
"""

import json
import re
from pathlib import Path

BASE_FOLDER = Path(__file__).parent
RULES_FILE = BASE_FOLDER / "data" / "grammar_rules.json"


def load_rules():
    """
    Read all grammar rules from the JSON file.
    Input:  nothing
    Output: a dictionary with keys: spelling, phrase_rules, third_person_verbs,
            helping_words, silent_h_words, you_sound_words
    """
    with open(RULES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def clean_word(word):
    """
    Remove punctuation from a single word and make it lowercase.
    Input:  "Goes," -> Output: "goes"
    """
    return word.lower().strip(".,!?;:\"'()")


def fix_spelling(sentence, spelling_list):
    """
    Replace commonly misspelled words with the correct spelling.
    Input:  sentence (string), spelling_list (dictionary wrong -> right)
    Output: (new_sentence, list_of_mistakes)
    """
    mistakes = []
    for wrong, right in spelling_list.items():
        # \b means "word boundary" so 'teh' is matched but 'tehran' is not.
        pattern = r"\b" + re.escape(wrong) + r"\b"
        sentence, count = re.subn(pattern, right, sentence, flags=re.IGNORECASE)
        if count > 0:
            mistakes.append(f"Spelling: **{wrong}** → **{right}**")
    return sentence, mistakes


def fix_phrases(sentence, phrase_rules):
    """
    Fix wrong word combinations such as 'i is', 'more better', 'could of'.
    Input:  sentence (string), phrase_rules (list of {wrong, right, rule})
    Output: (new_sentence, list_of_mistakes)
    """
    mistakes = []
    for rule in phrase_rules:
        pattern = r"\b" + re.escape(rule["wrong"]) + r"\b"
        sentence, count = re.subn(pattern, rule["right"], sentence, flags=re.IGNORECASE)
        if count > 0:
            mistakes.append(f"**{rule['wrong']}** → **{rule['right']}**: {rule['rule']}")
    return sentence, mistakes


def fix_subject_verb(sentence, verb_list, helping_words):
    """
    Fix he/she/it + base verb, e.g. 'he go' -> 'he goes'.
    It skips questions like 'Will he go?' because a helping word comes before 'he'.
    Input:  sentence, verb_list (go -> goes), helping_words (list)
    Output: (new_sentence, list_of_mistakes)
    """
    mistakes = []
    words = sentence.split()

    for i in range(len(words) - 1):
        subject = clean_word(words[i])
        verb = clean_word(words[i + 1])
        previous_word = clean_word(words[i - 1]) if i > 0 else ""

        if subject in ["he", "she", "it"] and verb in verb_list and previous_word not in helping_words:
            correct_verb = verb_list[verb]
            # replace only the verb part so punctuation like "go." stays as "goes."
            words[i + 1] = words[i + 1].lower().replace(verb, correct_verb, 1)
            mistakes.append(f"**{subject} {verb}** → **{subject} {correct_verb}**: "
                            f"with he/she/it the verb takes -s/-es in present simple.")

    return " ".join(words), mistakes


def needs_an(word, silent_h_words, you_sound_words):
    """
    Decide if a word needs 'an' (vowel sound) or 'a' (consonant sound).
    Input:  word (lowercase), two exception lists
    Output: True if 'an' is needed, otherwise False
    """
    if word in silent_h_words:        # hour, honest -> 'an'
        return True
    if word in you_sound_words:       # university, one -> 'a'
        return False
    return word[0] in "aeiou"


def fix_articles(sentence, silent_h_words, you_sound_words):
    """
    Fix 'a apple' -> 'an apple' and 'an book' -> 'a book'.
    Input:  sentence and the two exception lists
    Output: (new_sentence, list_of_mistakes)
    """
    mistakes = []
    words = sentence.split()

    for i in range(len(words) - 1):
        article = words[i].lower()
        next_word = clean_word(words[i + 1])

        if not next_word or not next_word[0].isalpha():
            continue                                  # skip numbers and symbols

        should_be_an = needs_an(next_word, silent_h_words, you_sound_words)

        if article == "a" and should_be_an:
            words[i] = "An" if words[i] == "A" else "an"
            mistakes.append(f"**a {next_word}** → **an {next_word}**: use 'an' before a vowel sound.")
        elif article == "an" and not should_be_an:
            words[i] = "A" if words[i] == "An" else "a"
            mistakes.append(f"**an {next_word}** → **a {next_word}**: use 'a' before a consonant sound.")

    return " ".join(words), mistakes


def remove_repeated_words(sentence):
    """
    Remove a word typed twice by mistake, e.g. 'the the book'.
    Output: (new_sentence, list_of_mistakes)
    """
    mistakes = []
    words = sentence.split()
    result = []

    for word in words:
        if result and clean_word(word) == clean_word(result[-1]) and clean_word(word) != "":
            mistakes.append(f"Repeated word: **{clean_word(word)} {clean_word(word)}**")
            continue                                  # do not add the repeated word
        result.append(word)

    return " ".join(result), mistakes


def fix_capitals_and_punctuation(sentence):
    """
    Capitalise the word 'I' and the first letter, and add a full stop if missing.
    Output: (new_sentence, list_of_mistakes)
    """
    mistakes = []

    # 'i' alone (also in i'm, i've) must always be capital
    new_sentence = re.sub(r"\bi\b", "I", sentence)
    if new_sentence != sentence:
        mistakes.append("The word **I** is always written with a capital letter.")
    sentence = new_sentence

    if sentence[0].islower():
        sentence = sentence[0].upper() + sentence[1:]
        mistakes.append("A sentence must start with a **capital letter**.")

    if sentence[-1] not in ".!?":
        sentence = sentence + "."
        mistakes.append("A sentence should end with a **full stop (.)**, **?** or **!**.")

    return sentence, mistakes


def check_sentence(sentence, rules):
    """
    Main function of this file: run every check one by one.
    Input:  sentence (string), rules (dictionary from load_rules)
    Output: (corrected_sentence, list_of_all_mistakes)
    """
    sentence = " ".join(sentence.split())      # remove extra spaces
    all_mistakes = []

    sentence, found = fix_spelling(sentence, rules["spelling"])
    all_mistakes += found

    sentence, found = fix_phrases(sentence, rules["phrase_rules"])
    all_mistakes += found

    sentence, found = fix_subject_verb(sentence, rules["third_person_verbs"], rules["helping_words"])
    all_mistakes += found

    sentence, found = fix_articles(sentence, rules["silent_h_words"], rules["you_sound_words"])
    all_mistakes += found

    sentence, found = remove_repeated_words(sentence)
    all_mistakes += found

    sentence, found = fix_capitals_and_punctuation(sentence)
    all_mistakes += found

    return sentence, all_mistakes


def build_check_reply(original, rules):
    """
    Turn the result of check_sentence into a friendly chat message.
    Input:  original sentence typed by the user, rules
    Output: (reply_text, number_of_mistakes)
    """
    corrected, mistakes = check_sentence(original, rules)

    if not mistakes:
        return "✅ **No mistakes found!** Your sentence looks correct.", 0

    reply = f"I found **{len(mistakes)}** thing(s) to fix:\n\n"
    for number, mistake in enumerate(mistakes, start=1):
        reply += f"{number}. {mistake}\n"
    reply += f"\n**Corrected sentence:**\n> {corrected}"
    return reply, len(mistakes)
