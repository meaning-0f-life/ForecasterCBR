import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
import os
from dotenv import load_dotenv
from app.llm.analyzer import LLMAnalyzer
from app.context_manager import get_context_manager
from app.data.fetcher import DataFetcher
from app.data.cache import DataCache
from app.utils.logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)

class TelegramAnalyzerBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not self.bot_token or self.bot_token == "your_bot_token_here":
            raise ValueError(
                "TELEGRAM_BOT_TOKEN not properly configured. "
                "Get a bot token from @BotFather on Telegram and set TELEGRAM_BOT_TOKEN in .env"
            )

        # Validate token format (bots tokens start with a number and contain a colon)
        if not self.bot_token.startswith(tuple("0123456789")) or ":" not in self.bot_token:
            raise ValueError("Invalid bot token format. Get a valid token from @BotFather")

        # Initialize bot properties (no parse mode to avoid HTML parsing issues)
        self.bot = Bot(token=self.bot_token)
        self.dp = Dispatcher()

        # Initialize components
        self.context_manager = get_context_manager()  # System context manager
        self.analyzer = LLMAnalyzer(
            model=os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free"),
            host=None  # For OpenRouter, no local host needed
        )

        # Register handlers (only for polling mode - no webhooks)
        self.dp.message.register(self.handle_start_command, Command(commands=["start"]))
        self.dp.message.register(self.handle_help_command, Command(commands=["help"]))
        self.dp.message.register(self.handle_text_message)  # Fallback for other messages

        # Start background task for Telegram data updates
        self._telegram_update_task = None

    def setup_webhook(self):
        """Set up webhook for production deployment."""
        if not self.production_webhook_url:
            return

        import requests
        webhook_url = f"{self.production_webhook_url}/telegram-webhook"
        telegram_api_url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"

        try:
            response = requests.post(telegram_api_url, data={"url": webhook_url})
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    logger.info(f"Webhook set successfully to: {webhook_url}")
                else:
                    logger.error(f"Failed to set webhook: {data.get('description')}")
            else:
                logger.error(f"HTTP error setting webhook: {response.status_code}")
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")

    async def handle_start_command(self, message: types.Message):
        """Handle /start command."""
        welcome_text = (
            "🤖 **CBR Анализатор**\n\n"
            "Я эксперт по монетарной политике Центрального банка России. "
            "Задайте мне любой вопрос о ключевой ставке ЦБ РФ, экономике, инфляции, "
            "прогнозах и других связанных темах.\n\n"
            "Я буду анализировать актуальные новости, экономические данные и "
            "историческую информацию для ответа.\n\n"
            "Примеры вопросов:\n"
            "• Какова текущая ключевая ставка?\n"
            "• Когда следующее заседание ЦБ РФ?\n"
            "• Что влияет на инфляцию в России?\n"
            "• Какой прогноз по ставке?\n\n"
            "Просто напишите ваш вопрос! 💬"
        )
        await message.reply(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def handle_help_command(self, message: types.Message):
        """Handle /help command."""
        welcome_text = (
            "❓ **Помощь**\n\n"
            "Я анализирую новости, экономические данные и научные статьи "
            "о монетарной политике ЦБ РФ.\n\n"
            "Задайте вопрос любым текстом - не нужно использовать специальные команды. "
            "Я пойму контекст и дам обоснованный ответ.\n\n"
            "Пример: `Расскажи о текущей ситуации с ключевой ставкой`"
        )
        await message.reply(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def handle_text_message(self, message: types.Message):
        """Handle general text messages (questions)."""
        user_question = message.text.strip()
        if not user_question:
            return

        logger.info(f"Received question from user {message.from_user.id}: {user_question}")

        # Send "thinking" message
        thinking_msg = await message.reply("🤔 Думаю над вашим вопросом...")

        try:
            # Get current system context (automatically updated every CACHE_TTL seconds)
            system_context = self.context_manager.get_context()

            # Answer using efficient system context approach
            answer = self.analyzer.answer_with_system_context(system_context, user_question)

            if answer:
                # Limit message length for Telegram (4096 chars)
                if len(answer) > 4000:
                    answer = answer[:4000] + "\n\n[Ответ сокращен для Telegram]"
                await message.reply(f"💡 {answer}")
            else:
                await message.reply(
                    "❌ Извините, не удалось обработать ваш вопрос. "
                    "Возможно, проблема с подключением к ИИ. Попробуйте позже."
                )

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await message.reply(
                "❌ Произошла ошибка при обработке запроса. Попробуйте перефразировать вопрос."
            )
        finally:
            # Delete thinking message
            try:
                await thinking_msg.delete()
            except:
                pass  # Message might be already deleted

    async def _update_telegram_data_background(self):
        """Background task to update Telegram data every CACHE_TTL seconds."""
        update_interval = int(os.getenv("CACHE_TTL", 3600))  # Default 1 hour
        while True:
            try:
                logger.info("Starting scheduled Telegram data update...")
                # Force update of Telegram data
                cache = DataCache(ttl=update_interval)
                fetcher = DataFetcher(
                    news_api_key=os.getenv("NEWS_API_KEY", ""),
                    economic_api_key=os.getenv("ECONOMIC_DATA_API_KEY", ""),
                    cache=cache,
                    telegram_api_id=int(os.getenv("TELEGRAM_API_ID", 0)) if os.getenv("TELEGRAM_API_ID") else None,
                    telegram_api_hash=os.getenv("TELEGRAM_API_HASH", "")
                )

                # Preload Telegram data (similar to preload_telegram_data.py)
                result = fetcher._fetch_news_from_telegram()
                if result and "centralbank_russia" in result:
                    logger.info("Scheduled Telegram data update successful")
                else:
                    logger.warning("Scheduled Telegram data update failed")

            except Exception as e:
                logger.error(f"Error in background Telegram update: {e}")

            # Wait for next update
            await asyncio.sleep(update_interval)

    async def start_polling(self):
        """Start the bot with polling."""
        logger.info("Starting Telegram bot polling...")

        # Start background task for Telegram updates
        if not self._telegram_update_task:
            self._telegram_update_task = asyncio.create_task(self._update_telegram_data_background())
            logger.info("Started background Telegram update task")

        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error starting bot polling: {e}")
            raise

    async def stop(self):
        """Stop the bot."""
        if self._telegram_update_task and not self._telegram_update_task.done():
            self._telegram_update_task.cancel()
            try:
                await self._telegram_update_task
            except asyncio.CancelledError:
                pass
            logger.info("Telegram background update task cancelled")

        await self.bot.session.close()
        logger.info("Telegram bot stopped")

# Global bot instance
telegram_bot: TelegramAnalyzerBot = None

def init_telegram_bot():
    """Initialize the telegram bot (called from main app)."""
    global telegram_bot
    if telegram_bot is None:
        telegram_bot = TelegramAnalyzerBot()
    return telegram_bot

async def start_telegram_bot():
    """Start the telegram bot (for background task)."""
    global telegram_bot
    if telegram_bot:
        await telegram_bot.start_polling()
    else:
        logger.error("Telegram bot not initialized")

async def stop_telegram_bot():
    """Stop the telegram bot."""
    global telegram_bot
    if telegram_bot:
        await telegram_bot.stop()
