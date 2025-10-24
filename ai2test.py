import sqlite3
from gpt4all import GPT4All
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
        "животные": ["животные", "биология", "природа", "исследование"],
        "природа": ["ландшафт", "биология", "парк", "исследование"],
        "писать": ["писать", "тексты", "копирайтинг"],
        "люди": ["люди", "общение", "персонал", "команда"],
        "анализ": ["анализ", "аналитика", "данные", "исследование"],
        "творчество": ["творчество", "дизайн", "создание", "креатив"]
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


def generate_ai_response(professions, user_input):
    if not professions:
        return "No relevant professions found in the database."

    names = [p['name'] for p in professions]

    
    db_info = [
        {
            "name": p["name"],
            "category": p["category"],
            "skills": p["skills"],
            "description": p["description"]
        }
        for p in professions
    ]

    prompt = f"""
You are a career advisor AI.
User input: "{user_input}"

Here is the ONLY data you are allowed to use (in JSON format):
{db_info}

Rules:
- Recommend ONLY from these professions: {', '.join(names)}.
- Do NOT invent or mention any professions not listed here.
- Write your answer in English.
- Use the given descriptions and skills only.
- If nothing fits, write exactly: "No relevant professions found in the database."
"""

    with model.chat_session():
        response = model.generate(prompt, max_tokens=250)
    return response.strip()


def generate_ai_detail(profession):
    prompt = f"""
You are a career advisor AI.
Use ONLY this data to describe the profession:

Name: {profession['name']}
Category: {profession['category']}
Personality type: {profession['personality_type']}
Skills: {profession['skills']}
Description: {profession['description']}

Rules:
- Write a clear short English description.
- Do not add new facts or other professions.
- Use only the provided data.
"""

    with model.chat_session():
        return model.generate(prompt, max_tokens=200).strip()



def get_ai_response(user_input, shown_ids):
    found = find_professions(user_input, shown_ids)
    if not found:
        return "No relevant professions found in the database.", shown_ids, None

    professions_to_show = found[:3]
    shown_ids.extend([p["id"] for p in professions_to_show])
    last_suggested = professions_to_show[0]["name"]

    ai_text = generate_ai_response(professions_to_show, user_input)
    translated = translate_to_rus(ai_text)
    return translated, shown_ids, last_suggested


def get_ai_detail(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM professions WHERE name=?", (name,))
    prof = cursor.fetchone()
    conn.close()
    if not prof:
        return "No information about this profession in the database."
    return generate_ai_detail(prof)


def console_interface():
    shown_ids = []
    last_suggested = None
    print("🤖 Career Bot started!")
    print("Type what you like or your skills. ('exit' = stop)")
    print("Type 'подробности' for more information.")

    while True:
        user_input = input("\nВаш запрос: ").strip().lower()

        if user_input in ("выход", "exit"):
            print("👋 Goodbye!")
            break
        if not user_input:
            continue

        if user_input in DETAIL_COMMANDS:
            if last_suggested:
                print("\nDetails:\n" + get_ai_detail(last_suggested))
            else:
                print("No profession selected yet.")
            continue

        response, shown_ids, last_suggested = get_ai_response(user_input, shown_ids)
        print("\nBot:")
        print(response)



if __name__ == "__main__":
    try:
        model = GPT4All(model_name=MODEL_NAME)
    except Exception as e:
        print("⚠️ Model failed to load:", e)
        model = None

    console_interface()
