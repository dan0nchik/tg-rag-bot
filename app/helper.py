import logging
from telebot import TeleBot, logger as telebot_logger
import config as config
from rag_engine import RagEngine
from datetime import datetime
from typing import Dict, List, Optional, Union, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
telebot_logger.setLevel(logging.INFO)


class MessageProcessor:
    """Handles message processing, history tracking, and RAG operations"""

    def __init__(self, rag_engine: RagEngine, history_size: int = 10):
        """Initialize the message processor with RAG engine and history settings"""
        self.rag = rag_engine
        self.history_size = history_size
        # State management
        self.current_doc: Dict[int, dict] = {}  # chat_id -> current document
        self.last_user: Dict[int, str] = {}  # chat_id -> username of last author
        self.last_messages: Dict[int, List[str]] = {}  # chat_id -> message history

    def format_user_message(self, username: str, text: str) -> str:
        """Format a message with username prefix"""
        return f"От {username}: {text}"

    def format_bot_response(self, bot_username: str, text: str) -> str:
        """Format a bot response with username prefix"""
        return f"От @{bot_username}: {text}"

    def add_to_history(self, chat_id: int, text: str) -> None:
        """Add message to chat history, maintaining history size limit"""
        history = self.last_messages.setdefault(chat_id, [])
        history.append(text)
        if len(history) > self.history_size:
            history.pop(0)

    def get_history(self, chat_id: int) -> List[str]:
        """Get message history for the specified chat"""
        return self.last_messages.get(chat_id, [])

    def create_document(
        self, chat_id: int, message_id: int, text: str, author: str
    ) -> dict:
        """Create a document object for indexing"""
        return {
            "id": f"{chat_id}_{message_id}",
            "text": text,
            "metadata": {
                "author": author,
                "date": datetime.now().isoformat(),
            },
        }

    def index_document(self, doc: dict) -> None:
        """Index a single document in the RAG engine"""
        self.rag.index_documents([doc])

    def flush_current_doc(self, chat_id: int) -> None:
        """Index and clear the current document buffer for a chat"""
        doc = self.current_doc.pop(chat_id, None)
        if doc:
            self.index_document(doc)

    def track_message(
        self, chat_id: int, message_id: int, username: str, text: str
    ) -> None:
        """Track a regular message, grouping consecutive messages by author"""
        formatted_text = self.format_user_message(username, text)
        self.add_to_history(chat_id, formatted_text)
        # Check if same user as before
        if self.last_user.get(chat_id) == username:
            # Same author - append to current document
            self.current_doc[chat_id]["text"] += f"\n{formatted_text}"
        else:
            # New author - flush previous and create new document
            self.flush_current_doc(chat_id)
            self.current_doc[chat_id] = self.create_document(
                chat_id, message_id, formatted_text, username
            )
            self.last_user[chat_id] = username

    def process_remember_command(
        self, chat_id: int, message_id: int, username: str, text: str
    ) -> str:
        """Process a 'remember' command and return confirmation"""
        formatted_text = self.format_user_message(username, text)
        doc = self.create_document(chat_id, message_id, formatted_text, username)
        self.index_document(doc)
        self.add_to_history(chat_id, formatted_text)
        return "✅ Запомнил"

    def process_all_command(self) -> str:
        """Processes @all command and returns a message mentioning all users"""
        return f"{config.DAN_USERNAME} {config.ALEX_USERNAME} {config.ARTEM_USERNAME} "

    def process_web_search(
        self,
        chat_id: int,
        message_id: int,
        bot_message_id: int,
        username: str,
        text: str,
        bot_username: str,
    ) -> str:
        """Process a web search request and return results"""
        formatted_text = self.format_user_message(username, text)
        self.add_to_history(chat_id, formatted_text)

        history = self.get_history(chat_id)
        result = self.rag.search_web(text, username, history)

        # Create and index bot response
        bot_text = self.format_bot_response(bot_username, result)
        self.add_to_history(chat_id, bot_text)

        bot_doc = self.create_document(
            chat_id, bot_message_id, bot_text, f"@{bot_username}"
        )
        self.index_document(bot_doc)

        return result

    def process_query(
        self,
        chat_id: int,
        message_id: int,
        bot_message_id: int,
        username: str,
        text: str,
        bot_username: str,
    ) -> str:
        """Process a RAG query and return response"""
        formatted_text = self.format_user_message(username, text)
        self.add_to_history(chat_id, formatted_text)

        history = self.get_history(chat_id)
        answer = self.rag.query(text, username, history)

        # Create and index bot response
        bot_text = self.format_bot_response(bot_username, answer)
        self.add_to_history(chat_id, bot_text)

        bot_doc = self.create_document(
            chat_id, bot_message_id, bot_text, f"@{bot_username}"
        )
        self.index_document(bot_doc)

        return answer
