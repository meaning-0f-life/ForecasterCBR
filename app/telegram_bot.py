import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
import os
from dotenv import load_dotenv
from app.llm.analyzer import LLMAnalyzer
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

        # Initialize bot properties
        bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)

        self.bot = Bot(token=self.bot_token, default=bot_properties)
        self.dp = Dispatcher()

        # Initialize components same as main app
        self.cache = DataCache(ttl=int(os.getenv("CACHE_TTL", 3600)))
        self.fetcher = DataFetcher(
            news_api_key=os.getenv("NEWS_API_KEY", ""),
            economic_api_key=os.getenv("ECONOMIC_DATA_API_KEY", ""),
            cache=self.cache
        )
        self.analyzer = LLMAnalyzer(
            model=os.getenv("OLLAMA_MODEL", "llama2"),
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )

        # Register handlers
        self.dp.message.register(self.handle_start_command, Command(commands=["start"]))
        self.dp.message.register(self.handle_help_command, Command(commands=["help"]))
        self.dp.message.register(self.handle_text_message)  # Fallback for other messages

    async def handle_start_command(self, message: types.Message):
        """Handle /start command."""
        welcome_text = (
            "🤖 <b>CBR Анализатор</b>\n\n"
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
        await message.reply(welcome_text)

    async def handle_help_command(self, message: types.Message):
        """Handle /help command."""
        welcome_text = (
            "❓ <b>Помощь</b>\n\n"
            "Я анализирую новости, экономические данные и научные статьи "
            "о монетарной политике ЦБ РФ.\n\n"
            "Задайте вопрос любым текстом - не нужно использовать специальные команды. "
            "Я пойму контекст и дам обоснованный ответ.\n\n"
            "Пример: <code>Расскажи о текущей ситуации с ключевой ставкой</code>"
        )
        await message.reply(welcome_text)

    async def handle_text_message(self, message: types.Message):
        """Handle general text messages (questions)."""
        user_question = message.text.strip()
        if not user_question:
            return

        logger.info(f"Received question from user {message.from_user.id}: {user_question}")

        # Send "thinking" message
        thinking_msg = await message.reply("🤔 Думаю над вашим вопросом...")

        try:
            # Get comprehensive data for analysis
            context_data = self.fetcher.get_combined_data()
            meeting_data = self.fetcher.get_cbr_meeting_dates()
            historical_rates = self.fetcher._fetch_cbr_key_rates_history()

            # Prepare comprehensive context
            comprehensive_data = {
                "cached_news_and_articles": context_data,
                "meeting_dates": meeting_data,
                "historical_key_rates": historical_rates,
                "current_inflation": self.fetcher._fetch_inflation_history(),
                "gdp_data": self.fetcher._fetch_gdp_history()
            }

            # Answer the question with full context
            answer = self.analyzer.answer_question_with_full_context(user_question, comprehensive_data)

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

    async def start_polling(self):
        """Start the bot with polling."""
        logger.info("Starting Telegram bot polling...")
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error starting bot polling: {e}")
            raise

    async def stop(self):
        """Stop the bot."""
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
