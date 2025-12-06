import ollama
from typing import Dict, Optional
from app.utils.logger import setup_logger
from .prompts import ANALYZE_KEY_RATE_PROMPT_RU, RATE_CHANGE_PROMPT_RU, NEXT_MEETING_PREDICTION_PROMPT_RU

logger = setup_logger(__name__)

class LLMAnalyzer:
    def __init__(self, model: str = "llama2", host: str = "http://localhost:11434"):
        self.model = model
        self.client = ollama.Client(host=host)

    def analyze_key_rate(self, data_text: str, news_data: str = "", economic_data: str = "") -> Optional[str]:
        """Analyze the key interest rate using LLM (Russian)."""
        try:
            prompt = ANALYZE_KEY_RATE_PROMPT_RU.format(
                news_data=news_data,
                economic_data=economic_data,
                data_text=data_text
            )
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            analysis = response["message"]["content"]
            logger.info("Key rate analysis completed")
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing key rate: {e}")
            return None

    def predict_rate_change(self, data_text: str) -> Optional[str]:
        """Predict if the rate will increase, decrease, or stay the same (Russian)."""
        try:
            prompt = RATE_CHANGE_PROMPT_RU.format(data_text=data_text)
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            prediction = response["message"]["content"]
            logger.info("Rate change prediction completed")
            return prediction
        except Exception as e:
            logger.error(f"Error predicting rate change: {e}")
            return None

    def predict_next_meeting_rate(self, data_text: str, next_meeting_date: str, upcoming_dates: list, historical_decisions: str) -> Optional[str]:
        """Predict the key rate after the next CBR meeting (Russian)."""
        try:
            prompt = NEXT_MEETING_PREDICTION_PROMPT_RU.format(
                next_meeting_date=next_meeting_date,
                upcoming_dates=", ".join(upcoming_dates[:5]) if upcoming_dates else "Недоступны",
                historical_decisions=historical_decisions,
                data_text=data_text
            )
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            prediction = response["message"]["content"]
            logger.info("Next meeting rate prediction completed")
            return prediction
        except Exception as e:
            logger.error(f"Error predicting next meeting rate: {e}")
            return None
