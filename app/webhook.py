from fastapi import APIRouter, Request, HTTPException
from app.llm.analyzer import LLMAnalyzer
from app.data.fetcher import DataFetcher
from app.data.cache import DataCache
from app.utils.logger import setup_logger
import json
import os
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)

router = APIRouter()

# Reuse components from main.py - in real app, use dependency injection or singleton
cache = DataCache(ttl=int(os.getenv("CACHE_TTL", 3600)))
fetcher = DataFetcher(
    news_api_key=os.getenv("NEWS_API_KEY", ""),
    economic_api_key=os.getenv("ECONOMIC_DATA_API_KEY", ""),
    cache=cache
)
analyzer = LLMAnalyzer(
    model=os.getenv("OLLAMA_MODEL", "llama2"),
    host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
)

@router.post("/dialogflow-webhook")
async def dialogflow_webhook(request: Request):
    """Handle Dialogflow webhook requests."""
    try:
        body = await request.json()
        logger.info(f"Received Dialogflow request: {json.dumps(body, ensure_ascii=False, indent=2)}")

        # Extract intent and parameters
        query_result = body.get("queryResult", {})
        intent = query_result.get("intent", {}).get("displayName", "")
        parameters = query_result.get("parameters", {})

        # Process based on intent
        fulfillment_text = process_intent(intent, parameters)

        # Dialogflow response format
        response = {
            "fulfillmentText": fulfillment_text
        }

        logger.info(f"Sending response: {fulfillment_text}")
        return response

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing error")

def process_intent(intent: str, parameters: dict) -> str:
    """Process the detected intent and generate response in Russian."""
    try:
        if intent == "AnalyzeKeyRate":
            data = fetcher.get_combined_data()
            analysis = analyzer.analyze_key_rate(data_text=data)
            return analysis or "Извините, не удалось проанализировать данные по ключевой ставке."
        
        elif intent == "PredictRateChange":
            data = fetcher.get_combined_data()
            prediction = analyzer.predict_rate_change(data_text=data)
            return prediction or "Не удалось сделать прогноз изменения ставки."

        elif intent == "PredictNextMeeting":
            data = fetcher.get_combined_data()
            meeting_data = fetcher.get_cbr_meeting_dates()

            next_date = meeting_data["next"]
            upcoming = meeting_data["upcoming"]
            past_rates = fetcher._fetch_cbr_key_rates_history()

            if not next_date:
                return "Нет информации о следующих заседаниях ЦБ РФ."

            prediction = analyzer.predict_next_meeting_rate(
                data_text=data,
                next_meeting_date=next_date,
                upcoming_dates=upcoming,
                historical_decisions=past_rates
            )
            return prediction or "Не удалось спрогнозировать ставку после следующего заседания."

        elif intent == "GetCurrentData":
            data = fetcher.get_combined_data()
            return f"Актуальные данные для анализа:\n\n{data}"

        elif intent == "GetMeetingDates":
            dates = fetcher.get_cbr_meeting_dates()
            past_str = ", ".join(dates["past"])
            upcoming_str = ", ".join(dates["upcoming"])
            next_date = dates["next"]

            response = f"""Даты заседаний ЦБ РФ:
Следующее заседание: {next_date or 'Не запланировано'}
Предстоящие: {upcoming_str or 'Нет данных'}
Прошлые (последние): {past_str}"""
            return response

    except Exception as e:
        logger.error(f"Error processing intent {intent}: {e}")
        return "Произошла ошибка при обработке запроса. Попробуйте позже."

    return "Извините, я не понимаю этот запрос. Попробуйте спросить об анализе ключевой ставки ЦБ РФ или датах заседаний."
