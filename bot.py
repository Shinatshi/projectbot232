import telebot
from config import TOKEN
from gpt4all import GPT4All
from career_core import get_ai_response, get_ai_detail

bot = telebot.TeleBot(TOKEN)
model = GPT4All(model_name="orca-mini-3b-gguf2-q4_0")

user_states = {}  


@bot.message_handler(commands=['start', 'help'])
def start(message):
    """
    Приветственное сообщение и инициализация состояния пользователя
    """
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я Career Bot.\n\n"
        "Напиши, что тебе нравится или какие у тебя навыки — и я предложу подходящие профессии.\n"
        "📝 Команды:\n"
        "• 'подробности' — показать описание последней профессии\n"
        "• 'выход' — завершить диалог"
    )
    user_states[message.chat.id] = {"shown_ids": [], "last_suggested": None}


@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    """
    Основная логика взаимодействия с пользователем
    """
    user_id = message.chat.id
    text = message.text.strip().lower()


    if user_id not in user_states:
        user_states[user_id] = {"shown_ids": [], "last_suggested": None}

    state = user_states[user_id]

    if text in ("выход", "exit", "quit"):
        bot.send_message(user_id, "👋 До встречи! Можешь вернуться в любое время.")
        user_states[user_id] = {"shown_ids": [], "last_suggested": None}
        return

    if text in ("подробности", "расскажи больше", "more"):
        if state["last_suggested"]:
            bot.send_chat_action(user_id, 'typing')
            detail = get_ai_detail(model, state["last_suggested"])
            bot.send_message(user_id, f"📘 {detail}")
        else:
            bot.send_message(user_id, "❌ Профессия пока не выбрана. Сначала задай запрос.")
        return

    
    bot.send_chat_action(user_id, 'typing')
    try:
        response, shown_ids, last_suggested = get_ai_response(model, text, state["shown_ids"])
        state["shown_ids"] = shown_ids
        state["last_suggested"] = last_suggested
        bot.send_message(user_id, f"🤖 {response}")

    
        if last_suggested:
            bot.send_message(user_id, "💡 Напиши «подробности», чтобы узнать больше об этой профессии.")
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Произошла ошибка: {e}")


if __name__ == "__main__":
    print("🚀 Career Bot запущен в Telegram...")
    bot.infinity_polling()
