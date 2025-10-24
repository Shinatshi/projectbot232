import sqlite3
import os


DB_NAME = 'career_bot.db'

def create_or_update_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE professions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            name TEXT,
            description TEXT,
            skills TEXT,
            personality_type TEXT,
            keywords TEXT
        )
        """)
        professions = [
            ("творчество", "дизайнер", "Создает визуальные решения для брендов", "Figma, Photoshop", "креативный", "творчество, самовыражение, креативность"),
            ("творчество", "копирайтер", "Пишет тексты для рекламы и сайтов", "Письмо, креативность", "креативный", "творчество, самовыражение, тексты"),
            ("технологии", "программист", "Решает задачи с помощью кода", "Python, логика", "аналитик", "кодирование, технологии, разработка"),
            ("технологии", "аналитик данных", "Анализирует данные для бизнеса", "Excel, SQL, Python", "аналитик", "аналитика, данные, цифры"),
            ("общение", "HR-специалист", "Работает с людьми, помогает командам", "коммуникация, эмпатия", "эмпатичный", "общение, люди, взаимодействие"),
            ("общение", "коуч", "Помогает людям развиваться", "слушание, мотивация", "эмпатичный", "коучинг, развитие, помощь"),
            ("природа", "ландшафтный дизайнер", "Создает зеленые зоны и парки", "AutoCAD, планирование", "креативный", "природа, дизайн, ландшафт"),
            ("природа", "биолог", "Исследует растения и животных", "наблюдательность, аналитика", "исследователь", "природа, биология, исследование")
        ]
        cursor.executemany("""
            INSERT INTO professions (category, name, description, skills, personality_type, keywords) 
            VALUES (?, ?, ?, ?, ?, ?)""", professions)
        conn.commit()
        conn.close()
        print("✅ База данных создана и заполнена.")
    else:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(professions)")
        columns = [col[1] for col in cursor.fetchall()]
        if "keywords" not in columns:
            cursor.execute("ALTER TABLE professions ADD COLUMN keywords TEXT DEFAULT ''")
        conn.commit()
        conn.close()
