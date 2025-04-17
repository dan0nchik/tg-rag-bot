import logging
from telebot import TeleBot, logger as telebot_logger
import config
from rag_engine import RagEngine
from datetime import datetime

# Логирование
logging.basicConfig(level=logging.INFO)
telebot_logger.setLevel(logging.INFO)

# Параметр: сколько последних сообщений хранить в истории
N_LAST_MESSAGES = getattr(config, "N_LAST_MESSAGES", 10)

# Создаем экземпляр бота и RAG‑движок
bot: TeleBot = TeleBot(config.TELEGRAM_TOKEN)
rag = RagEngine()

# Буферы для группировки и история
current_doc = {}  # chat_id -> текущий документ {id, text, metadata}
last_user = {}  # chat_id -> username последнего автора
last_messages = {}  # chat_id -> list последних текстов (sliding window)


def add_to_history(chat_id: int, text: str):
    """
    Добавляет text в историю chat_id, сохраняя не более N_LAST_MESSAGES записей.
    Реализовано как sliding window: append, а если слишком много — pop(0).
    """
    buf = last_messages.setdefault(chat_id, [])
    buf.append(text)
    if len(buf) > N_LAST_MESSAGES:
        buf.pop(0)


def flush_current_doc(chat_id: int):
    """
    Отправляет на индексирование накопленный текущий документ (если есть)
    и очищает его.
    """
    doc = current_doc.pop(chat_id, None)
    if doc:
        rag.index_documents([doc])


# 1) Ответ на упоминание @botusername
@bot.message_handler(
    func=lambda m: m.text and m.text.strip().startswith(f"@{config.BOT_USERNAME}")
)
def handle_mention_commands(message):
    chat_id = message.chat.id
    username = f"@{message.from_user.username}"
    text = (
        "От "
        + username
        + ": "
        + message.text.replace(f"@{config.BOT_USERNAME}", "", 1).strip()
    )

    if not text:
        return bot.reply_to(
            message,
            f"❗️ Укажи вопрос после @{config.BOT_USERNAME}.\n"
            f"Пример: @{config.BOT_USERNAME} Как дела?",
        )

    # "запомни" — отдельная индексация этого сообщения
    if "запомни" in text.lower():
        doc = {
            "id": f"{chat_id}_{message.message_id}",
            "text": text,
            "metadata": {
                "author": username,
                "date": datetime.now().isoformat(),
            },
        }
        rag.index_documents([doc])
        add_to_history(chat_id, text)
        return bot.reply_to(message, "✅ Запомнил")

    # Сохраняем упоминание пользователя в историю
    add_to_history(chat_id, text)

    # Собираем историю
    history = last_messages.get(chat_id, [])
    bot.send_chat_action(chat_id, "typing")
    answer = rag.query(text, username, history)

    # отправляем ответ и сохраняем объект Message
    reply_msg = bot.reply_to(message, answer)

    # сохраняем ответ бота в истории и индексируем как отдельный документ
    add_to_history(chat_id, f"От @{config.BOT_USERNAME}: {answer}")
    bot_doc = {
        "id": f"{chat_id}_{reply_msg.message_id}",
        "text": f"От @{config.BOT_USERNAME}: {answer}",
        "metadata": {
            "author": f"@{config.BOT_USERNAME}",
            "date": datetime.now().isoformat(),
        },
    }
    rag.index_documents([bot_doc])


# 2) Ответ на реплай к собственному сообщению бота с поддержкой "запомни"
@bot.message_handler(
    func=lambda m: m.reply_to_message
    and m.reply_to_message.from_user
    and m.reply_to_message.from_user.username == config.BOT_USERNAME
)
def handle_reply_to_bot(message):
    chat_id = message.chat.id
    username = f"@{message.from_user.username}"
    text = f"От {username}: {message.text.strip()}"

    if not text:
        return

    # "запомни" — отдельная индексация
    if "запомни" in text.lower():
        doc = {
            "id": f"{chat_id}_{message.message_id}",
            "text": text,
            "metadata": {
                "author": username,
                "date": datetime.now().isoformat(),
            },
        }
        rag.index_documents([doc])
        add_to_history(chat_id, text)
        return bot.reply_to(message, "✅ Запомнил")

    # Сохраняем ответ пользователя в историю
    add_to_history(chat_id, text)

    # Обычный запрос
    history = last_messages.get(chat_id, [])
    bot.send_chat_action(chat_id, "typing")
    answer = rag.query(text, username, history)

    reply_msg = bot.reply_to(message, answer)

    # сохраняем ответ бота в истории и индексируем как отдельный документ
    add_to_history(chat_id, f"От @{config.BOT_USERNAME}: {answer}")
    bot_doc = {
        "id": f"{chat_id}_{reply_msg.message_id}",
        "text": f"От @{config.BOT_USERNAME}: {answer}",
        "metadata": {
            "author": f"@{config.BOT_USERNAME}",
            "date": datetime.now().isoformat(),
        },
    }
    rag.index_documents([bot_doc])


# 3) Трекинг всех прочих текстовых сообщений:
#    группируем подряд идущие сообщения от одного автора,
#    индекcируем при смене автора.
@bot.message_handler(
    func=lambda m: m.text and not m.text.strip().startswith(f"@{config.BOT_USERNAME}")
)
def track_messages(message):
    chat_id = message.chat.id
    username = f"@{message.from_user.username}"
    text = f"От {username}: {message.text}"

    # обновляем историю sliding window
    add_to_history(chat_id, text)

    # проверяем: есть ли текущий документ, и автор тот же?
    if last_user.get(chat_id) == username:
        # тот же автор — просто дописываем текст
        current_doc[chat_id]["text"] += "\n" + text
    else:
        # новый автор: сначала флашим предыдущий документ
        flush_current_doc(chat_id)
        # создаём новый
        current_doc[chat_id] = {
            "id": f"{chat_id}_{message.message_id}",
            "text": text,
            "metadata": {
                "author": username,
                "date": datetime.now().isoformat(),
            },
        }
        last_user[chat_id] = username


if __name__ == "__main__":
    logging.info("Бот запущен")
    bot.infinity_polling(timeout=20, long_polling_timeout=5, skip_pending=False)
