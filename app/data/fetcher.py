import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from app.utils.logger import setup_logger
from .cache import DataCache

logger = setup_logger(__name__)

class DataFetcher:
    def __init__(self, news_api_key: str, economic_api_key: str, cache: DataCache):
        self.news_api_key = news_api_key
        self.economic_api_key = economic_api_key
        self.cache = cache
        self.news_api_url = "https://newsapi.org/v2/everything"
        self.cbr_key_rate_url = "https://www.cbr.ru/currency_base/inflation_report/"  # Placeholder for actual API
        # CBR API endpoints (actual URLs may need adjustment)
        self.cbr_api_base = "https://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx"
        # For economic data, might need to use alternative sources
        self.economic_api_url = "https://www.alphavantage.co/query"

        # Scientific articles folder
        self.articles_folder = os.path.join(os.path.dirname(__file__), "../../articles")

    def fetch_news_data(self, keywords: str = "ЦБ РФ ключевая ставка инфляция экономика") -> Optional[str]:
        """Fetch latest news data related to CBR and Russian economy."""
        cache_key = {"type": "news", "keywords": keywords}
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info("Using cached news data")
            return cached_data

        try:
            # Get news from last 7 days
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            params = {
                "q": keywords,
                "apiKey": self.news_api_key,
                "language": "ru",
                "sortBy": "publishedAt",
                "from": from_date
            }
            response = requests.get(self.news_api_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract relevant articles
            articles = data.get("articles", [])[:15]  # More articles for better context
            news_text = ""
            for art in articles:
                if art['description']:
                    news_text += f"- {art['publishedAt'][:10]} {art['title']}: {art['description']}\n"

            self.cache.set(cache_key, news_text)
            logger.info("Fetched and cached news data")
            return news_text
        except Exception as e:
            logger.error(f"Error fetching news data: {e}")
            return None

    def fetch_historical_economic_data(self) -> Optional[str]:
        """Fetch historical economic data from CBR and other sources."""
        cache_key = {"type": "historical_economic"}
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info("Using cached historical economic data")
            return cached_data

        try:
            # CBR Key Rates History (simulated API call)
            # In real implementation, you might need to scrape from CBR website
            # Or use third-party economic data providers
            cbr_data = self._fetch_cbr_key_rates_history()

            # Fetch inflation data
            inflation_data = self._fetch_inflation_history()

            # Fetch other indicators if available
            gdp_data = self._fetch_gdp_history()

            text = f"""
Исторические данные ЦБ РФ:
{cbr_data}

Инфляция (история):
{inflation_data}

ВВП (если доступно):
{gdp_data}
            """

            self.cache.set(cache_key, text)
            return text
        except Exception as e:
            logger.error(f"Error fetching historical economic data: {e}")
            return None

    def _fetch_cbr_key_rates_history(self) -> str:
        """Fetch CBR key rates historical data."""
        # Placeholder - in real app, implement CBR API or scraping
        # CBR publishes rate history, you can download from their website
        return """
История ключевых ставок ЦБ РФ (последние 2 года):
- 2024-02-23: 16.00%
- 2024-01-26: 16.00%
- 2024-01-15: 16.00%
- 2023-12-15: 16.00%
- И т.д. (данные нужно загрузить с сайта ЦБ РФ: cbr.ru)
        """

    def _fetch_inflation_history(self) -> str:
        """Fetch inflation history for Russia."""
        try:
            params = {
                "function": "INFLATION",
                "apikey": self.economic_api_key,
                "datatype": "json"
            }
            response = requests.get(self.economic_api_url, params=params)
            response.raise_for_status()
            data = response.json()

            if "data" in data:
                inflation_entries = data["data"][:12]  # Last 12 months
                text = "\n".join([f"- {entry['date']}: {entry.get('value', 'N/A')}%" for entry in inflation_entries])
                return text
            else:
                return "Нет данных по инфляции (требуется API ключ Alpha Vantage)"
        except Exception as e:
            return f"Ошибка получения данных инфляции: {e}"

    def _fetch_gdp_history(self) -> str:
        """Fetch GDP history if available."""
        # Placeholder - GDP data might be available from ROSSTAT or other sources
        return "Данные по ВВП доступны на сайте Росстата: rosstat.gov.ru"

    def fetch_scientific_articles(self) -> str:
        """Load scientific articles from the articles folder."""
        if not os.path.exists(self.articles_folder):
            os.makedirs(self.articles_folder)
            return "Папка для статей создана. Поместите текстовые файлы статей в папку articles/ рядом с requirements.txt."

        articles_text = "Научные статьи (загрузите статьи в папку articles/):\n\n"
        try:
            txt_files = [f for f in os.listdir(self.articles_folder) if f.endswith('.txt')]
            for filename in txt_files[:5]:  # Limit to 5 articles
                filepath = os.path.join(self.articles_folder, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()[:5000]  # Limit content length
                    articles_text += f"=== {filename} ===\n{content}\n\n"
            return articles_text
        except Exception as e:
            logger.error(f"Error loading scientific articles: {e}")
            return f"Ошибка загрузки статей: {e}"

    def get_cbr_meeting_dates(self) -> Dict[str, List[str]]:
        """Get past and upcoming CBR meeting dates."""
        # CBR usually meets every ~1.5 months, adjust dates as per schedule
        # In real app, implement web scraping from cbr.ru or API if available
        past_dates = [
            "2024-02-23", "2024-01-26", "2023-12-15", "2023-11-10", "2023-09-15"
        ]
        upcoming_dates = [
            "2024-04-26", "2024-06-14", "2024-07-26", "2024-10-11", "2024-11-15"
        ]
        return {
            "past": past_dates,
            "upcoming": upcoming_dates,
            "next": upcoming_dates[0] if upcoming_dates else None
        }

    def get_combined_data(self) -> str:
        """Get comprehensive combined data including history and articles."""
        news = self.fetch_news_data()
        economic_historical = self.fetch_historical_economic_data()
        articles = self.fetch_scientific_articles()

        combined = f"""
ПОСЛЕДНИЕ НОВОСТИ:
{news or 'Нет новостных данных'}

ИСТОРИЧЕСКИЕ ЭКОНОМИЧЕСКИЕ ДАННЫЕ:
{economic_historical or 'Нет исторических данных'}

НАУЧНЫЕ СТАТЬИ:
{articles or 'Нет статей (загрузите в папку articles/)'}
        """
        return combined
