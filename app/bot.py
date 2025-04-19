import logging
from telebot import TeleBot, logger as telebot_logger
import config as config
from helper import MessageProcessor
from rag_engine import RagEngine
from typing import Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
telebot_logger.setLevel(logging.INFO)


class RagBot:
    """Telegram bot with RAG integration"""

    def __init__(self, token: str, bot_username: str, history_size: int = 10):
        """Initialize the bot with configuration"""
        self.bot = TeleBot(token)
        self.bot_username = bot_username
        self.processor = MessageProcessor(RagEngine(), history_size)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Configure message handlers"""
        self.bot.message_handler(
            func=lambda m: m.text and m.text.strip().startswith(f"@{self.bot_username}")
        )(self._create_mention_handler())

        self.bot.message_handler(
            func=lambda m: m.reply_to_message
            and m.reply_to_message.from_user
            and m.reply_to_message.from_user.username == self.bot_username
        )(self._create_reply_handler())

        self.bot.message_handler(
            func=lambda m: m.text
            and not m.text.strip().startswith(f"@{self.bot_username}")
        )(self.handle_regular_message)

    def _create_mention_handler(self) -> Callable:
        """Create handler for mention commands"""

        def handler(message):
            chat_id = message.chat.id
            username = self._get_username(message)
            text = self._extract_mention_text(message)

            if not text:
                self.bot.reply_to(
                    message,
                    f"❗️ Укажи вопрос после @{self.bot_username}.\n"
                    f"Пример: @{self.bot_username} Как дела?",
                )
                return

            self._process_command(message, chat_id, username, text)

        return handler

    def _create_reply_handler(self) -> Callable:
        """Create handler for replies to bot messages"""

        def handler(message):
            chat_id = message.chat.id
            username = self._get_username(message)
            text = message.text.strip()

            if not text:
                return

            self._process_command(message, chat_id, username, text)

        return handler

    def _process_command(self, message, chat_id: int, username: str, text: str) -> None:
        """Central command processing logic for both mentions and replies"""
        # Handle "remember" command
        if self._is_remember_command(text):
            response = self.processor.process_remember_command(
                chat_id, message.message_id, username, text
            )
            self.bot.reply_to(message, response)
            return

        self.bot.send_chat_action(chat_id, "typing")

        # Handle web search command
        if self._is_web_search_command(text):
            reply_msg = self.bot.reply_to(message, "Ищу информацию...")
            result = self.processor.process_web_search(
                chat_id,
                message.message_id,
                reply_msg.message_id,
                username,
                text,
                self.bot_username,
            )
            self.bot.edit_message_text(
                result, chat_id=chat_id, message_id=reply_msg.message_id
            )
            return

        # Handle normal RAG query
        reply_msg = self.bot.reply_to(message, "Обрабатываю запрос...")
        answer = self.processor.process_query(
            chat_id,
            message.message_id,
            reply_msg.message_id,
            username,
            text,
            self.bot_username,
        )
        self.bot.edit_message_text(
            answer, chat_id=chat_id, message_id=reply_msg.message_id
        )

    def _get_username(self, message) -> str:
        """Extract username from message"""
        return f"@{message.from_user.username}"

    def _is_remember_command(self, text: str) -> bool:
        """Check if text contains a remember command"""
        return "запомни" in text.lower()

    def _is_web_search_command(self, text: str) -> bool:
        """Check if text contains a web search command"""
        return "загугли" in text.lower()

    def _extract_mention_text(self, message) -> str:
        """Extract text after bot mention"""
        return message.text.replace(f"@{self.bot_username}", "", 1).strip()

    def handle_regular_message(self, message) -> None:
        """Handle regular text messages"""
        chat_id = message.chat.id
        username = self._get_username(message)
        text = message.text

        self.processor.track_message(chat_id, message.message_id, username, text)

    def run(self) -> None:
        """Start the bot and begin polling for messages"""
        logging.info("Бот запущен")
        self.bot.infinity_polling(
            timeout=20, long_polling_timeout=5, skip_pending=False
        )


def main():
    """Main entry point for the application"""
    bot = RagBot(
        token=config.TELEGRAM_TOKEN,
        bot_username=config.BOT_USERNAME,
        history_size=getattr(config, "N_LAST_MESSAGES", 10),
    )
    logging.info("Бот инициализирован")
    bot.run()


if __name__ == "__main__":
    main()
