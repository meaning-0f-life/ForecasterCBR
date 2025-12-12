from fastapi import APIRouter, Request, HTTPException
from app.utils.logger import setup_logger
from app.llm.analyzer import LLMAnalyzer
from app.context_manager import get_context_manager as get_context_manager_instance
import os
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)

router = APIRouter()

# Initialize components lazily
context_manager = None
analyzer = None

def get_context_mgr():
    global context_manager
    if context_manager is None:
        context_manager = get_context_manager_instance()
    return context_manager

def get_analyzer():
    global analyzer
    if analyzer is None:
        analyzer = LLMAnalyzer(
            model=os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free"),
            host=None  # For OpenRouter
        )
    return analyzer

@router.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Telegram webhook for bot messages."""
    try:
        data = await request.json()

        if "message" not in data:
            return {"ok": True}

        message = data["message"]
        user_question = message.get("text", "").strip()

        if not user_question:
            return {"ok": True}

        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]

        logger.info(f"Received question from user {user_id}: {user_question}")

        # IMMEDIATE response to Telegram to avoid timeout
        # Process the request asynchronously
        import asyncio
        asyncio.create_task(process_telegram_message_async(chat_id, user_question, user_id))

        return {"ok": True}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_telegram_message_async(chat_id: int, user_question: str, user_id: int):
    """Process Telegram message asynchronously to avoid webhook timeouts."""
    try:
        # Get current system context
        ctx_mgr = get_context_mgr()
        system_context = ctx_mgr.get_context()

        # Generate answer
        llm_analyzer = get_analyzer()
        answer = llm_analyzer.answer_with_system_context(system_context, user_question)

        if answer:
            # Limit message length for Telegram
            if len(answer) > 4000:
                answer = answer[:4000] + "\n\n[Ответ сокращен для Telegram]"
        else:
            answer = "❌ Извините, не удалось обработать ваш вопрос. Попробуйте позже."

        # Send response back to Telegram
        import requests
        telegram_url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": answer,
            "parse_mode": "Markdown"
        }

        response = requests.post(telegram_url, data=data)
        if response.status_code == 200:
            logger.info(f"Sent answer to chat {chat_id}")
        else:
            logger.error(f"Failed to send message: {response.text}")

    except Exception as e:
        logger.error(f"Error processing Telegram message: {e}")
        # Try to send error message
        try:
            telegram_url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": "❌ Произошла ошибка при обработке запроса.",
            }
            requests.post(telegram_url, data=data)
        except:
            pass

@router.post("/dialogflow-webhook")
async def dialogflow_webhook(request: Request):
    """DEPRECATED: Dialogflow webhook - no longer used. Use Telegram bot instead."""
    logger.warning("Dialogflow webhook called - this endpoint is deprecated")
    return {"message": "Dialogflow integration deprecated. Use Telegram bot instead.", "deprecated": True}
