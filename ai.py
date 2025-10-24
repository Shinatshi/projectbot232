import sqlite3
import os
from gpt4all import GPT4All
from create import create_or_update_db
from translate import translate_to_rus

DB_NAME = 'career_bot.db'
MODEL_NAME = "orca-mini-3b-gguf2-q4_0"
DETAIL_COMMANDS = ["подробности", "расскажи больше", "more"]
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def find_professions(user_query, shown_ids):
    STOP_WORDS = {"мне", "нравится", "и", "а", "но", "что", "когда", "хочу", "интересно"}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM professions")
    rows = cursor.fetchall()
    conn.close()

    words = [
        w.strip(".,!?()").lower()
        for w in user_query.split()
        if w.lower() not in STOP_WORDS
    ]
    if not words:
        return []

    synonym_map = {
        "код": ["код", "программирование", "разработка", "программист"],
        "животные": ["биология", "природа", "иследованние"],
        "писать": ["писать", "тексты", "копирайтинг"],
        "люди": ["общение", "команда", "персонал"],
        "анализ": ["аналитика", "данные", "исследование"],
        "творчество": ["дизайн", "креатив", "создание"],
    }
    expanded_words = set(words)
    for w in words:
        if w in synonym_map:
            expanded_words.update(synonym_map[w])


    scored = []
    for row in rows:
        text = " ".join([
            row["name"], row["category"], row["description"],
            row["skills"], row["keywords"]
        ]).lower()

        score = sum(1 for w in expanded_words if w in text)
        if score >= 2 and row["id"] not in shown_ids:
            scored.append((score, row))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [r for _, r in scored]


try:
    model = GPT4All(model_name=MODEL_NAME)
except Exception as e:
    print("Модель не загрузилась:", e)
    model = None

def get_ai_detail(profession_name):
    if model:
        with model.chat_session():
            ai_text = model.generate(
                f"You are a career consultant. Describe the profession '{profession_name}' in detail. "
                f"Explain what this person does, their main responsibilities, required skills, "
                f"and what type of person this career suits. Keep it clear and friendly.",
                max_tokens=250
            )
        return ai_text
    else:
        return get_profession_detail(profession_name)

def get_ai_response(user_input, shown_ids):
    found = find_professions(user_input, shown_ids)
    if not found:
        if model:
            with model.chat_session():
                ai_text = model.generate(
    f"You are a career consultant. Your task is to help people choose a profession based on their interests. "
    f"Interests: {user_input}. "
    f"Suggest a few suitable professions or career paths and explain why they might fit. "
    f"Do not repeat the request or ask questions.",
    max_tokens=250
)
            translated = translate_to_rus(ai_text)
            return translated, shown_ids, None
        else:
            return "Ничего не смог найти", shown_ids, None

    prof = found[0]
    shown_ids.append(prof["id"])
    last_suggested = prof["name"]

    if model:
        with model.chat_session():
            ai_text = model.generate(
    f"You are a career consultant. Your task is to help people choose a profession based on their interests. "
    f"User interests: {user_input}. "
    f"Give 2–3 possible professions or career paths that logically combine these interests. "
    f"Explain briefly why each might fit. "
    f"Do not ask any questions, do not ask for clarification, and do not request more details. "
    f"If the combination is unusual, make creative suggestions instead of asking.",
    max_tokens=300
)
        translated = translate_to_rus(ai_text)
        return translated, shown_ids, last_suggested
    else:
        card = (
            f"Я думаю, тебе может подойти профессия: {prof['name']} "
            f"(категория: {prof['category']}).\n"
            f"Если хочешь, можешь спросить подробнее об этой профессии."
        )
        return card, shown_ids, last_suggested

def get_profession_detail(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM professions WHERE name=?", (name,))
    prof = cursor.fetchone()
    conn.close()
    if not prof:
        return "Ничего не найдено"
    skills_list = prof["skills"].split(", ")
    detail = (
        f"Профессия: {prof['name']}\n"
        f"Категория: {prof['category']}\n"
        f"Тип личности: {prof['personality_type']}\n"
        f"Навыки: {', '.join(skills_list)}\n"
        f"Описание: {prof['description']}"
    )
    return detail


def console_interface():
    shown_ids = []
    last_suggested = None
    print("🤖 Карьерный бот запущен!")
    print("Напиши, что тебе нравится или какие у тебя навыки. ('выход'=остановка)")
    print("Подробности = больше информации")

    while True:
        user_input = input("\nВаш запрос: ").strip().lower()

        if user_input in ("выход", "exit"):
            print("👋 До встречи!")
            break
        if not user_input:
            continue

        
        if user_input in DETAIL_COMMANDS:
            if last_suggested:
                detail = get_ai_detail(last_suggested)
                print("\nПодробности:\n" + detail)
            else:
                print("-")
            continue  

        
        response, shown_ids, last_suggested = get_ai_response(user_input, shown_ids)
        print("\nБот:")
        print(response)


if __name__ == "__main__":
    create_or_update_db()
    console_interface()
