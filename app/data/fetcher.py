import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from app.utils.logger import setup_logger
from .cache import DataCache

# Для парсинга данных ЦБ РФ
import urllib.parse

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
        self.cbr_key_rate_url = "https://www.cbr.ru/hd_base/KeyRate/"
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
        """Fetch CBR key rates historical data from cbr.ru by parsing interactive chart"""
        cache_key = {"type": "cbr_key_rates_parsed"}
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info("Using cached parsed CBR key rates data")
            return cached_data

        try:
            # Main CBR key rate page with interactive chart
            url = "https://www.cbr.ru/hd_base/KeyRate/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            logger.info("Successfully loaded CBR key rates page, parsing chart data...")

            # Parse chart data from Highcharts JavaScript configuration
            scripts = soup.find_all('script')
            dates_list = []
            rates_float = []

            for script in scripts:
                if script.string:
                    script_text = script.string

                    # Extract series data (contains rate values)
                    series_start_pattern = r'"series"\s*:\s*\['
                    series_start_match = re.search(series_start_pattern, script_text, re.DOTALL)
                    if series_start_match:
                        start_pos = series_start_match.end()

                        # Find matching closing bracket for series array
                        series_content = script_text[start_pos:]
                        bracket_count = 0
                        end_pos = 0
                        for i, char in enumerate(series_content):
                            if char == '[':
                                bracket_count += 1
                            elif char == ']':
                                bracket_count -= 1
                                if bracket_count == -1:
                                    end_pos = i
                                    break

                        if end_pos > 0:
                            series_data = series_content[:end_pos]

                            # Extract data array from series
                            data_start_pattern = r'"data"\s*:\s*\['
                            data_start_match_relative = re.search(data_start_pattern, series_data, re.DOTALL)
                            if data_start_match_relative:
                                data_start_pos = data_start_match_relative.end()

                                # Find matching closing bracket for data array
                                data_content = series_data[data_start_pos:]
                                data_bracket_count = 0
                                data_end_pos = 0
                                for j, char in enumerate(data_content):
                                    if char == '[':
                                        data_bracket_count += 1
                                    elif char == ']':
                                        data_bracket_count -= 1
                                        if data_bracket_count == -1:
                                            data_end_pos = j
                                            break

                                if data_end_pos > 0:
                                    data_str = data_content[:data_end_pos]

                                    try:
                                        # Parse rate values
                                        data_values = re.findall(r'(\d+[\.,]\d+|\d+)', data_str)
                                        rates_float = [float(val.replace(',', '.')) for val in data_values if val.strip()]

                                        # Extract categories (dates)
                                        categories_start_pattern = r'"categories"\s*:\s*\['
                                        categories_start_match = re.search(categories_start_pattern, script_text, re.DOTALL)
                                        if categories_start_match:
                                            cat_start_pos = categories_start_match.end()

                                            # Find matching closing bracket for categories array
                                            cat_content = script_text[cat_start_pos:]
                                            cat_bracket_count = 0
                                            cat_end_pos = 0
                                            for k, char in enumerate(cat_content):
                                                if char == '[':
                                                    cat_bracket_count += 1
                                                elif char == ']':
                                                    cat_bracket_count -= 1
                                                    if cat_bracket_count == -1:
                                                        cat_end_pos = k
                                                        break

                                            if cat_end_pos > 0:
                                                categories_str = cat_content[:cat_end_pos]
                                                dates_list = re.findall(r'"([^"]+)"', categories_str)

                                                logger.info(f"Extracted {len(dates_list)} dates and {len(rates_float)} rates from chart")
                                                break  # Found the data, exit script loop
                                    except Exception as e:
                                        logger.error(f"Error parsing chart data: {e}")
                                        continue

            # Validate and format the extracted data
            if not dates_list or not rates_float or len(dates_list) != len(rates_float):
                logger.warning("Could not extract complete date-rate pairs from chart, using fallback data")
                return self._get_fallback_key_rates_data()

            # Pair dates with rates
            paired_data = list(zip(dates_list, rates_float))

            # Format the data
            history_text = "КЛЮЧЕВЫЕ СТАВКИ ЦБ РФ (из интерактивного графика на cbr.ru):\n\n"

            # Add current rate (most recent)
            if paired_data:
                current_date, current_rate = paired_data[-1]
                history_text += f"ТЕКУЩАЯ СТАВКА: {current_rate:.2f}% ({current_date})"
                history_text += "\n\nПОЛНАЯ ИСТОРИЯ (последние 50 изменений):\n"
                for date, rate in paired_data[-50:]:
                    history_text += f"- {date}: {rate:.2f}%\n"
            else:
                logger.warning("No paired data available, using fallback")
                return self._get_fallback_key_rates_data()

            history_text += "Источник: Банк России - интерактивный график ключевых ставок\n"
            history_text += f"Всего записей: {len(paired_data)}\n"
            history_text += "Обновлено: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.cache.set(cache_key, history_text)
            logger.info(f"Successfully parsed {len(paired_data)} key rate records from CBR chart")
            return history_text

        except Exception as e:
            logger.error(f"Error scraping CBR key rates from chart: {e}")
            return self._get_fallback_key_rates_data()

    def _get_fallback_key_rates_data(self) -> str:
        """Fallback hardcoded data for key rates when scraping fails"""
        logger.info("Using fallback key rates data")
        return """
АКТУАЛЬНЫЕ КЛЮЧЕВЫЕ СТАВКИ ЦБ РФ (рекомендуем проверить на сайте cbr.ru):

ТЕКУЩАЯ СТАВКА: 21.00% (установлена 8 февраля 2025 года)

ИСТОРИЯ ИЗМЕНЕНИЙ (2025-2024 гг.):
05.12.2025	16,50
04.12.2025	16,50
03.12.2025	16,50
02.12.2025	16,50
01.12.2025	16,50
28.11.2025	16,50

ПРИМЕЧАНИЕ: Данные нужно актуализировать на сайте ЦБ РФ
Обновлено: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
