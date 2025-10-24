import sqlite3

conn = sqlite3.connect("career_bot.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM professions")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
