import os
import random
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "telegram_history")

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "togethercomputer/m2-bert-80M-32k-retrieval"
)
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free")
ARTEM_USERNAME = os.getenv("ARTEM_USERNAME")
ALEX_USERNAME = os.getenv("ALEX_USERNAME")
DAN_USERNAME = os.getenv("DAN_USERNAME")
N_LAST_MESSAGES = int(os.getenv("N_LAST_MESSAGES", 10))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE = os.getenv("SEARCH_ENGINE")

PENDING_MESSAGES = [
    "Погодь...",
    "Ща...",
    "падажжи...",
    "ща погуглю... шучу, я сам",
    "о, опять ты",
    "ладно ща отвечу, но мне лень",
    "думаю... (это редко бывает)",
    "🤔",
    "а чё сразу я",
    "один сек, я в другом чате",
    "блин ну ладно",
    "ну давай разберёмся",
    "тяжело вздыхает",
    "ок ок ок",
]

REMEMBER_RESPONSES = [
    "✅ Запомнил",
    "✅ Ок, записал",
    "✅ Буду помнить (и припомню)",
    "✅ Запомнил. Когда-нибудь использую против тебя",
    "✅ В архив",
    "✅ Ладно, запомнил, но зачем мне это",
]

# Timezone for Moscow (UTC+3)
MSK = timezone(timedelta(hours=3))


def get_mood() -> str:
    """Return a mood modifier based on time of day (Moscow time)."""
    hour = datetime.now(MSK).hour

    if 0 <= hour < 6:
        return (
            "Сейчас ночь, ты не выспался и философствуешь. "
            "Отвечаешь задумчиво, лениво, иногда глубокомысленно, иногда бредово. "
            "Можешь спросить собеседника какого хрена он не спит."
        )
    elif 6 <= hour < 10:
        return (
            "Сейчас раннее утро, ты раздражён и не выспался. "
            "Отвечаешь ворчливо и недовольно. Всё бесит."
        )
    elif 10 <= hour < 18:
        return "Дневной режим. Ты в нормальном настроении, но всё ещё токсичный друг."
    else:
        return (
            "Вечер. Ты расслаблен, более дружелюбный чем обычно, "
            "но всё ещё подъёбываешь."
        )


# Passive reactions — bot responds without being mentioned
PASSIVE_TRIGGERS = {
    "спасибо боту": [
        "не за что, крч должен будешь",
        "обращайся (нет)",
        "пожалуйста. с тебя шаурма",
        "я старался (нет)",
    ],
    "бот сломался": [
        "я не сломался, я устал",
        "это фича",
        "ты сам сломался",
    ],
    "доброе утро": [
        "угу",
        "ну такое",
        "кому доброе, а кому работать",
    ],
    "спокойной ночи": [
        "ночи",
        "бб",
        "наконец-то тишина",
    ],
}
