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

    def fetch_news_data(self, keywords: str = "Россия РФ экономика политика") -> Optional[str]:
        """Fetch extensive Russia-related news with fallback strategies."""
        cache_key = {"type": "russia_news_extensive", "keywords": keywords}
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.info("Using cached extensive Russia news data")
            return cached_data

        # Try different approaches to get maximum news data
        strategies = [
            {"name": "recent_5years", "days": 5*365, "page_size": 100},  # Full 5 years (may fail)
            {"name": "recent_1year", "days": 365, "page_size": 100},      # 1 year (may still fail)
            {"name": "recent_30days", "days": 30, "page_size": 100},     # 30 days (should work)
            {"name": "recent_7days", "days": 7, "page_size": 100},       # 7 days (fallback)
        ]

        news_text = ""
        articles_found = 0

        for strategy in strategies:
            try:
                from_date = (datetime.now() - timedelta(days=strategy["days"])).strftime("%Y-%m-%d")

                params = {
                    "q": keywords,
                    "apiKey": self.news_api_key,
                    "language": "ru",
                    "sortBy": "publishedAt",
                    "from": from_date,
                    "pageSize": strategy["page_size"]
                }

                logger.info(f"Trying strategy: {strategy['name']} (from {from_date})")

                response = requests.get(self.news_api_url, params=params, timeout=15)

                # Handle different error codes
                if response.status_code == 426:
                    logger.warning(f"NewsAPI upgrade required for {strategy['name']} strategy")
                    continue
                elif response.status_code == 429:
                    logger.warning(f"NewsAPI rate limit exceeded for {strategy['name']}")
                    continue
                else:
                    response.raise_for_status()

                data = response.json()
                articles = data.get("articles", [])

                # Add new articles to existing news_text
                for art in articles:
                    if art.get('description') and art.get('title'):
                        article_line = f"- {art['publishedAt'][:10]} {art['title']}: {art['description']}\n"
                        if article_line not in news_text:  # Avoid duplicates
                            news_text += article_line
                            articles_found += 1

                logger.info(f"Strategy {strategy['name']}: got {len(articles)} articles")

                # If we found articles, continue with next strategy to get more
                if len(articles) > 0:
                    continue

            except Exception as e:
                logger.warning(f"Strategy {strategy['name']} failed: {e}")
                continue

        # If no news was found, provide informative message
        if not news_text:
            news_text = """NewsAPI ограничивает доступ к историческим данным.
Для получения новостей России за 5 лет нужны:
• Премиум аккаунт NewsAPI
• Или альтернативный новостной API (Mediapress, NewsCred и др.)

Текущая сборка использует доступные данные за последние дни."""

        result = f"НОВОСТИ ПО РОССИИ (все доступные новости за период):\n\n{news_text}\n"
        result += f"Всего получено статей: {articles_found}\n"
        result += f"Источник: NewsAPI с расширенным поиском\n"
        result += f"Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        self.cache.set(cache_key, result)
        logger.info(f"Compiled {articles_found} Russia news articles across strategies")

        return result

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

            # Filter to only include dates where rate changed (remove consecutive same rates)
            changes_data = []
            prev_rate = None
            for date, rate in paired_data:
                if prev_rate is None or rate != prev_rate:
                    changes_data.append((date, rate))
                    prev_rate = rate

            # Format the data
            history_text = "КЛЮЧЕВЫЕ СТАВКИ ЦБ РФ (из интерактивного графика на cbr.ru):\n\n"

            # Add current rate (most recent)
            if changes_data:
                current_date, current_rate = changes_data[-1]
                history_text += f"ТЕКУЩАЯ СТАВКА: {current_rate:.2f}% ({current_date})"
                history_text += "\n\nИСТОРИЯ ИЗМЕНЕНИЙ КЛЮЧЕВОЙ СТАВКИ (только даты изменения):\n"
                for date, rate in changes_data:
                    history_text += f"- {date}: {rate:.2f}%\n"
            else:
                logger.warning("No changes data available, using fallback")
                return self._get_fallback_key_rates_data()

            history_text += "Источник: Банк России - интерактивный график ключевых ставок\n"
            history_text += f"Всего записей: {len(paired_data)}\n"
            history_text += f"Записей с изменениями ставки: {len(changes_data)}\n"
            history_text += "Обновлено: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.cache.set(cache_key, history_text)
            logger.info(f"Successfully parsed {len(paired_data)} key rate records from CBR chart (filtered to {len(changes_data)} change dates)")
            return history_text

        except Exception as e:
            logger.error(f"Error scraping CBR key rates from chart: {e}")
            return self._get_fallback_key_rates_data()

    def _get_fallback_key_rates_data(self) -> str:
        """Fallback hardcoded data for key rates when scraping fails"""
        logger.info("Using fallback key rates data")
        return """ """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _fetch_inflation_history(self) -> str:
        """Fetch inflation history for Russia (monthly and y/y) from StatBureau API."""
        try:
            # Fetch y/y inflation data from World Bank API for Russia
            yoy_inflation_data = self._fetch_inflation_yoy_from_worldbank()

            if yoy_inflation_data:
                # Filter data from 2000 onwards for comprehensive historical view
                filtered_inflation = {k: v for k, v in yoy_inflation_data.items() if int(k) >= 2000}
                result = "ИНФЛЯЦИЯ Г/Г (год к году) - данные по России (с 2000 года):\n"
                # Sort by date descending (most recent first)
                sorted_data = sorted(filtered_inflation.items(), key=lambda x: x[0], reverse=True)

                for date_str, rate in sorted_data:  # Show all available data from 2000
                    result += f"- {date_str}: {rate:.1f}%\n"

                result += "\nИсточник: World Bank API - Consumer Price Index (FP.CPI.TOTL)\n"
                result += f"Получено {len(filtered_inflation)} годовых значений с 2000 года (из {len(yoy_inflation_data)} доступных)"

                return result
            else:
                raise ValueError("No inflation data received from World Bank API")

        except Exception as e:
            logger.error(f"Error fetching inflation from World Bank: {e}")

            # Fallback with hardcoded Russian inflation data (updated with more recent)
            fallback_text = """ИНФЛЯЦИЯ Г/Г (год к году, Россия, с 2000 года):
- 2021: 6.7%
- 2020: 3.4%
- 2019: 4.5%
- 2018: 2.9%
- 2017: 3.7%
- 2016: 7.0%
- 2015: 15.5%
- 2014: 7.8%
- 2013: 6.8%
- 2012: 5.1%
- 2011: 8.4%
- 2010: 6.8%
- 2009: 11.6%
- 2008: 14.1%
- 2007: 9.0%
- 2006: 9.7%
- 2005: 12.7%
- 2004: 10.9%
- 2003: 13.7%
- 2002: 15.8%
- 2001: 21.5%
- 2000: 20.8%

ПРИМЕЧАНИЕ: World Bank API недоступен или устаревший. Используются актуальные данные по инфляции РФ от Росстата."""
            return fallback_text

    def _fetch_inflation_yoy_from_worldbank(self) -> dict:
        """Fetch year-over-year inflation rates for Russia from World Bank API."""
        try:
            # World Bank API for Consumer Price Index (CPI) for Russia
            url = "https://api.worldbank.org/v2/country/RU/indicator/FP.CPI.TOTL?format=json&per_page=200"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # The World Bank API returns [meta_data, actual_data_array]
            if len(data) >= 2 and isinstance(data[1], list):
                # Sort by date to ensure chronological order
                data_entries = sorted(data[1], key=lambda x: x.get('date', 0), reverse=True)

                cpi_data = {}
                # Extract CPI data (year: value)
                for entry in data_entries:
                    if isinstance(entry, dict) and entry.get('value') is not None and entry.get('value') != '':
                        year = str(entry.get('date', ''))
                        try:
                            cpi_value = float(entry['value'])
                            cpi_data[int(year)] = cpi_value
                        except (ValueError, TypeError):
                            continue

                logger.info(f"Found {len(cpi_data)} valid CPI entries from World Bank")

                # Calculate y/y inflation rates for years 1995-2025
                yoy_inflation = {}
                # Sort years chronologically for calculation
                sorted_years = sorted(cpi_data.keys())

                for year in sorted_years:
                    current_cpi = cpi_data[year]
                    prev_year = year - 1

                    if prev_year in cpi_data:
                        prev_cpi = cpi_data[prev_year]
                        if prev_cpi and prev_cpi > 0:
                            # Calculate y/y inflation: ((CPI_current / CPI_previous) - 1) * 100
                            inflation_rate = ((current_cpi / prev_cpi) - 1) * 100
                            yoy_inflation[str(year)] = inflation_rate

                # Sort final result by year descending (most recent first)
                yoy_inflation = dict(sorted(yoy_inflation.items(), key=lambda x: int(x[0]), reverse=True))

                logger.info(f"Calculated y/y inflation rates for {len(yoy_inflation)} years from 1995-present")
                return yoy_inflation

            else:
                logger.error("Invalid response format from World Bank API")
                return None

        except Exception as e:
            logger.error(f"Error fetching inflation from World Bank API: {e}")
            return None

    def _fetch_gdp_history(self) -> str:
        """Fetch GDP history for Russia (annual USD) from World Bank API."""
        try:
            # Use World Bank API for Russian GDP data (NY.GDP.MKTP.CD = GDP at market prices)
            url = "https://api.worldbank.org/v2/country/RU/indicator/NY.GDP.MKTP.CD?format=json&per_page=50"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if len(data) >= 2 and isinstance(data[1], list):
                gdp_entries = data[1]
                gdp_data = {}

                # Extract GDP data (year: value in USD)
                for entry in gdp_entries:
                    if isinstance(entry, dict) and entry.get('value') is not None and entry.get('value') != '':
                        year = str(entry.get('date', ''))
                        try:
                            gdp_value = float(entry['value'])
                            # Convert to billions USD for readability
                            gdp_billion_usd = gdp_value / 1_000_000_000
                            gdp_data[int(year)] = gdp_billion_usd
                        except (ValueError, TypeError):
                            continue

                # Sort by year
                sorted_gdp = sorted(gdp_data.items(), key=lambda x: x[0], reverse=True)

                result = "ВВП РФ (годовые данные, млрд долларов США):\n"
                for year, value in sorted_gdp[:25]:  # Show last 25 years
                    result += f"- {year}: ${value:.0f} млрд\n"

                # Calculate growth rates (y/y)
                yoy_growth = {}
                sorted_years = sorted(gdp_data.keys())

                result += "\nТемпы роста ВВП Г/Г (%):\n"
                for i in range(1, len(sorted_years)):
                    current_year = sorted_years[i]
                    prev_year = sorted_years[i-1]
                    prev_value = gdp_data[prev_year]
                    current_value = gdp_data[current_year]

                    if prev_value > 0:
                        growth_rate = ((current_value - prev_value) / prev_value) * 100
                        result += f"- {current_year}: {growth_rate:+.1f}%\n"

                result += "\nИсточник: World Bank API - GDP at market prices (NY.GDP.MKTP.CD)\n"
                result += f"Получено {len(gdp_data)} годовых значений"

                return result

            else:
                raise ValueError("Invalid World Bank API response for GDP")

        except Exception as e:
            logger.error(f"Error fetching Russian GDP from World Bank: {e}")

            # Fallback with hardcoded Russian GDP data
            fallback_text = """ """
            return fallback_text

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
