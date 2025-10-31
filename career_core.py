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
    STOP_WORDS = {"мне", "нравится", "и", "а", "но", "что", "когда", "хочу", "интересно", "быть", "стать", "это"}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM professions")
    rows = cursor.fetchall()
    conn.close()

    # Разбиваем запрос на слова
    words = [
        w.strip(".,!?()").lower()
        for w in user_query.split()
        if w.lower() not in STOP_WORDS
    ]
    if not words:
        return []

    synonym_map = {
        "творчество": ["творчество", "созидание", "создание", "креатив", "креативность", "дизайн", "фантазия", "воображение", "самовыражение", "арт", "искусство"],
        "дизайн": ["дизайн", "рисование", "оформление", "визуал", "иллюстрация", "графика", "стиль", "композиция"],
        "рисование": ["рисование", "иллюстрация", "графика", "живопись", "эскиз", "творчество"],
        "креатив": ["креатив", "творчество", "дизайн", "идеи", "вдохновение", "креативный", "оригинальный","креативным","креативной"],
        "код": ["код", "программирование", "разработка", "айти", "it", "python", "java", "c++", "js", "технологии", "инженерия", "техника"],
        "программирование": ["программирование", "код", "программист", "разработка", "software", "айти"],
        "технологии": ["технологии", "it", "айти", "компьютеры", "интернет", "разработка", "инновации"],
        "аналитика": ["анализ", "аналитика", "данные", "цифры", "исследование", "таблицы", "excel", "sql", "логика"],
        "люди": ["люди", "общение", "психология", "помощь", "персонал", "команда", "эмпатия", "мотивация", "обучение", "наставничество", "коучинг"],
        "общение": ["общение", "контакт", "люди", "взаимодействие", "разговор", "переговоры", "слушание"],
        "коуч": ["коуч", "наставник", "тренер", "психолог", "помощник", "мотивация", "помощь"],
        "hr": ["hr", "персонал", "рекрутинг", "команда", "работа с людьми", "эмпатия", "подбор", "человеческие ресурсы"],
        "природа": ["природа", "экология", "ландшафт", "растения", "животные", "окружающая среда", "зелень", "парк", "сад", "планета"],
        "животные": ["животные", "биология", "зоология", "исследование", "экология", "уход", "питомцы"],
        "биология": ["биология", "животные", "растения", "исследование", "природа", "ученый", "анализ"],
        "создание": ["создание", "проект", "разработка", "творчество", "созидание"],
        "помощь": ["помощь", "поддержка", "сотрудничество", "взаимопомощь"],
        "развитие": ["развитие", "рост", "обучение", "мотивация", "наставничество"],
    }

    expanded_words = set(words)
    for w in words:
        for key, syns in synonym_map.items():
            if w == key or w in syns:
                expanded_words.update(syns)

    scored = []
    for row in rows:
        text = " ".join([
            row["name"],
            row["category"],
            row["description"],
            row["skills"],
            row["keywords"]
        ]).lower()

        score = sum(1 for w in expanded_words if w in text)
        if score >= 1 and row["id"] not in shown_ids:
            scored.append((score, row))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [r for _, r in scored]


def generate_ai_response(model, professions, user_input):
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
"""

    with model.chat_session():
        response = model.generate(prompt, max_tokens=250)
    return response.strip()


def generate_ai_detail(model, profession):
    prompt = f"""
You are a career advisor AI.
Use ONLY this data to describe the profession:

Name: {profession['name']}
Category: {profession['category']}
Personality type: {profession['personality_type']}
Skills: {profession['skills']}
Description: {profession['description']}

Rules:
- Write a short English description.
- Do not add new facts.
"""

    with model.chat_session():
        return model.generate(prompt, max_tokens=200).strip()


def get_ai_response(model, user_input, shown_ids):
    found = find_professions(user_input, shown_ids)
    if not found:
        return "No relevant professions found in the database.", shown_ids, None

    professions_to_show = found[:3]
    shown_ids.extend([p["id"] for p in professions_to_show])
    last_suggested = professions_to_show[0]["name"]

    ai_text = generate_ai_response(model, professions_to_show, user_input)
    translated = translate_to_rus(ai_text)
    return translated, shown_ids, last_suggested


def get_ai_detail(model, name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM professions WHERE name=?", (name,))
    prof = cursor.fetchone()
    conn.close()
    if not prof:
        return "No information about this profession in the database."
    english_detail = generate_ai_detail(model, prof)
    translated_detail = translate_to_rus(english_detail)
    return translated_detail
