import os
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
    "Подожди...",
    "погоди...",
    "Ща...",
    "Погоди-ка, я ща...",
    "ща все будет...",
    "ок щас...",
    "падажжи...",
]
