import ollama
from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Optional DeepSeek support
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai library not available. DeepSeek support disabled.")

from app.utils.logger import setup_logger
from .prompts import ANALYZE_KEY_RATE_PROMPT_RU, RATE_CHANGE_PROMPT_RU, NEXT_MEETING_PREDICTION_PROMPT_RU, GENERAL_QA_PROMPT_RU, COMPREHENSIVE_QA_PROMPT_RU, SYSTEM_QA_PROMPT_RU

load_dotenv()

logger = setup_logger(__name__)

class LLMAnalyzer:
    def __init__(self, model: str = None, host: str = None):
        # Determine which model provider to use
        self.use_deepseek = os.getenv("USE_DEEPSEEK").lower() == "true"

        if self.use_deepseek:
            # Use DeepSeek cloud model
            if not OPENAI_AVAILABLE:
                raise ValueError("DeepSeek support requested but openai library not available")

            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = os.getenv("DEEPSEEK_BASE_URL")

            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY not set in environment")

            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.model = os.getenv("DEEPSEEK_MODEL")
            self.provider = "DeepSeek"
            logger.info(f"Initialized DeepSeek analyzer with model: {self.model}")
        else:
            # Use local Ollama model
            self.client = ollama.Client(host=host or os.getenv("OLLAMA_HOST"))
            self.model = model or os.getenv("OLLAMA_MODEL")
            self.provider = "Ollama"
            logger.info(f"Initialized Ollama analyzer with model: {self.model}")

    def _chat_completion(self, messages: list) -> str:
        """Unified method for getting completions from different providers."""
        if self.use_deepseek:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2048,
                temperature=0.7
            )
            return response.choices[0].message.content
        else:
            response = self.client.chat(
                model=self.model,
                messages=messages
            )
            return response["message"]["content"]

    def analyze_key_rate(self, data_text: str, news_data: str = "", economic_data: str = "") -> Optional[str]:
        """Analyze the key interest rate using LLM (Russian)."""
        try:
            prompt = ANALYZE_KEY_RATE_PROMPT_RU.format(
                news_data=news_data,
                economic_data=economic_data,
                data_text=data_text
            )
            analysis = self._chat_completion([{"role": "user", "content": prompt}])
            logger.info("Key rate analysis completed")
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing key rate: {e}")
            return None

    def predict_rate_change(self, data_text: str) -> Optional[str]:
        """Predict if the rate will increase, decrease, or stay the same (Russian)."""
        try:
            prompt = RATE_CHANGE_PROMPT_RU.format(data_text=data_text)
            prediction = self._chat_completion([{"role": "user", "content": prompt}])
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
            prediction = self._chat_completion([{"role": "user", "content": prompt}])
            logger.info("Next meeting rate prediction completed")
            return prediction
        except Exception as e:
            logger.error(f"Error predicting next meeting rate: {e}")
            return None

    def answer_question(self, user_question: str, context_data: str) -> Optional[str]:
        """Answer user's question using all available context data (Russian)."""
        try:
            prompt = GENERAL_QA_PROMPT_RU.format(
                user_question=user_question,
                context_data=context_data
            )
            answer = self._chat_completion([{"role": "user", "content": prompt}])
            logger.info("General question answered")
            return answer
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return None

    def answer_question_with_full_context(self, user_question: str, comprehensive_data: Dict) -> Optional[str]:
        """Answer user's question using comprehensive full context (Russian)."""
        try:
            # Format all data into a comprehensive context
            context_parts = []

            # News and articles
            news_articles = comprehensive_data.get("cached_news_and_articles", "")
            context_parts.append(f"=== НОВОСТИ И СТАТЬИ ===\n{news_articles}")

            # Meeting dates
            meeting_data = comprehensive_data.get("meeting_dates", {})
            meeting_info = f"Следующее заседание: {meeting_data.get('next', 'Не запланировано')}\n"
            meeting_info += f"Предстоящие: {', '.join(meeting_data.get('upcoming', []))}\n"
            meeting_info += f"Прошлые: {', '.join(meeting_data.get('past', []))}"
            context_parts.append(f"=== ДАТЫ ЗАСЕДАНИЙ ЦБ РФ ===\n{meeting_info}")

            # Historical key rates
            historical_rates = comprehensive_data.get("historical_key_rates", "")
            context_parts.append(f"=== ИСТОРИЯ КЛЮЧЕВЫХ СТАВОК ===\n{historical_rates}")

            # Current inflation
            inflation_data = comprehensive_data.get("current_inflation", "")
            context_parts.append(f"=== ТЕКУЩИЕ ДАННЫЕ ПО ИНФЛЯЦИИ ===\n{inflation_data}")

            # GDP data
            gdp_data = comprehensive_data.get("gdp_data", "")
            context_parts.append(f"=== ДАННЫЕ ПО ВВП ===\n{gdp_data}")

            # Combine all context
            full_context = "\n\n".join(context_parts)

            prompt = COMPREHENSIVE_QA_PROMPT_RU.format(
                user_question=user_question,
                full_context=full_context
            )

            answer = self._chat_completion([{"role": "user", "content": prompt}])
            logger.info("Comprehensive question answered with full context")
            return answer
        except Exception as e:
            logger.error(f"Error answering question with full context: {e}")
            return None

    def answer_with_system_context(self, system_context: str, user_question: str) -> Optional[str]:
        """Answer user's question using system context (efficient approach)."""
        try:
            # Use simple question prompt with system context
            prompt = SYSTEM_QA_PROMPT_RU.format(
                system_context=system_context,
                user_question=user_question
            )

            answer = self._chat_completion([{"role": "user", "content": prompt}])
            logger.info("Question answered using system context")
            return answer
        except Exception as e:
            logger.error(f"Error answering with system context: {e}")
            return None
