#!/usr/bin/env python3
"""
Тестовый скрипт для проверки парсинга данных с сайта ЦБ РФ
Использование: python test_cbr_scraping.py
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cbr_scraping():
    """Тестирование парсинга данных с сайта ЦБ РФ"""

    print("🔍 Начинаем тестирование парсинга данных ЦБ РФ\n")

    # 1. Основная страница ключевых ставок
    main_url = "https://www.cbr.ru/hd_base/KeyRate/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        print("1. Загружаем основную страницу...")
        response = requests.get(main_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        print("   ✅ Страница загружена успешно\n")

        # 2. Ищем все процентные значения
        page_text = soup.get_text()
        percentages = re.findall(r'\d{1,2}(?:[.,]\d{1,2})?%', page_text)
        unique_percentages = sorted(list(set(float(p.replace(',', '.')) for p in percentages)))

        print("2. Найденные значения процентов на странице:")
        for pct in unique_percentages[-10:]:  # Показать последние 10
            print(pct)

        # 3. Ищем таблицы с данными
        tables = soup.find_all('table')
        print(f"3. Найдено таблиц: {len(tables)}")

        rate_data_found = False
        for i, table in enumerate(tables):
            rows = table.find_all('tr')

            # Проверяем заголовки
            if rows:
                headers_row = rows[0]
                header_cols = headers_row.find_all(['th', 'td'])
                header_texts = [col.get_text(strip=True) for col in header_cols]

                # Ищем таблицы связанные со ставками
                if any(keyword in ' '.join(header_texts).upper() for keyword in ['СТАВК', 'RATE', 'ПРОЦЕНТ', 'DATE']):
                    print(f"\n   📊 Таблица {i+1} выглядит многообещающе:")
                    print(f"   Заголовки: {header_texts}")

                    # Показываем первые 3 строки данных
                    for row in rows[1:4]:
                        cols = row.find_all(['td', 'th'])
                        col_texts = [col.get_text(strip=True) for col in cols]
                        if col_texts:
                            print(f"   Данные: {col_texts}")
                            rate_data_found = True

        if not rate_data_found:
            print("   ❌ Таблицы со ставками не найдены явно")

        # 4. Проверяем JavaScript данные
        print("\n4. Ищем данные в JavaScript переменных...")
        scripts = soup.find_all('script')
        js_data_found = False
        chart_rates_found = False

        for script in scripts:
            if script.string:
                script_text = script.string

                # Ищем массивы данных
                data_patterns = [
                    r'"data"\s*:\s*"([^"]+)"',
                    r'KeyRateData\s*=\s*(\[.*?\])',
                    r'hd_key_rate\s*=\s*(\{.*?\})',
                    r'chart\s*data\s*=\s*(\[.*?\])'
                ]

                for pattern in data_patterns:
                    matches = re.findall(pattern, script_text, re.DOTALL | re.IGNORECASE)
                    for match in matches:
                        if len(match) > 10:  # Фильтруем слишком короткие строки
                            print(f"   ✅ Найден JavaScript паттерн: {match[:100]}...")
                            js_data_found = True

                # Новый поиск: данные чарта в Highcharts конфигурации
                series_start_pattern = r'"series"\s*:\s*\['
                series_start_match = re.search(series_start_pattern, script_text, re.DOTALL)
                if series_start_match:
                    start_pos = series_start_match.end()

                    # Найдем конец массива series - первая ] после start_pos с учетом вложенности
                    series_content = script_text[start_pos:]
                    bracket_count = 0
                    end_pos = 0
                    for i, char in enumerate(series_content):
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                            if bracket_count == -1:  # Закрывающая ] для "series":[
                                end_pos = i
                                break

                    if end_pos > 0:
                        series_data = series_content[:end_pos]

                        # Ищем данные ставки внутри series
                        data_start_pattern = r'"data"\s*:\s*\['
                        data_start_match_relative = re.search(data_start_pattern, series_data, re.DOTALL)
                        if data_start_match_relative:
                            data_start_pos = data_start_match_relative.end()

                            # Найдем конец массива data
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
                                    # Парсим данные ставки
                                    data_values = re.findall(r'(\d+[\.,]\d+|\d+)', data_str)
                                    rates_float = [float(val.replace(',', '.')) for val in data_values if val.strip()]

                                    # Ищем даты
                                    categories_start_pattern = r'"categories"\s*:\s*\['
                                    categories_start_match = re.search(categories_start_pattern, script_text, re.DOTALL)
                                    if categories_start_match:
                                        cat_start_pos = categories_start_match.end()

                                        # Найдем конец массива categories
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

                                            # Сопоставляем даты и ставки
                                            if len(dates_list) >= len(rates_float):
                                                print("   📊 ✅ Найден чарт ключевых ставок с данными:")
                                                print(f"   Столбец дат: {len(dates_list)} значений с {dates_list[0]} по {dates_list[-1]}")
                                                print(f"   Столбец ставок: {len(rates_float)} значений с {rates_float[0]:.2f}% по {rates_float[-1]:.2f}%")
                                                latest_rates = list(zip(dates_list[-10:], rates_float[-10:]))
                                                print("   Последние 10 значений:")
                                                for date_str, rate in latest_rates:
                                                    print(".2f")
                                                chart_rates_found = True
                                                print("   ✅ Данные чарта успешно извлечены")
                                            else:
                                                print(f"   ⚠️  Несоответствие количества дат ({len(dates_list)}) и ставок ({len(rates_float)})")
                                except Exception as e:
                                    print(f"   ❌ Ошибка парсинга данных чарта: {e}")

        if chart_rates_found:
            js_data_found = True

        if not js_data_found:
            print("   ❌ JavaScript данные не найдены")

        # 5. Ищем ссылки на файлы данных
        print("\n5. Ищем ссылки на файлы данных...")
        data_links = soup.find_all('a', href=re.compile(r'\.(xls|xlsx|csv|json)$|export|download', re.IGNORECASE))

        if data_links:
            print("   📁 Найденные ссылки на файлы данных:")
            for link in data_links[:5]:  # Первые 5
                href = link.get('href')
                text = link.get_text(strip=True)[:50]
                print(f"   - {text}: {href}")
        else:
            print("   ❌ Ссылки на файлы данных не найдены")

        # 6. Рекомендации
        print("\n📋 РЕЗУЛЬТАТЫ АНАЛИЗА:")
        print("   ✅ Процентные данные найдены:", len(unique_percentages), "уникальных значений")
        print("   " + ("✅" if rate_data_found else "❌"), "Явные таблицы со ставками", ("найдены" if rate_data_found else "не найдены"))
        print("   " + ("✅" if js_data_found else "❌"), "JavaScript данные", ("найдены" if js_data_found else "не найдены"))

        if unique_percentages:
            # Найдем наиболее вероятную актуальную ставку
            current_rates = [p for p in unique_percentages if 5.0 <= p <= 30.0]  # Реалистичный диапазон
            if current_rates:
                most_recent_rate = max(current_rates)  # Предполагаем что максимальна актуальна
                print(most_recent_rate)
            else:
                print("⚠️ Ни одно процентное значение не находится в реалистичном диапазоне")
        else:
            print("   ⚠️ Процентные значения на странице не найдены")

        print("\n🔄 РЕКОМЕНДАЦИИ:")
        if not rate_data_found and not js_data_found:
            print("   1. Данные могут загружаться AJAX-ом - попробуйте проверить Network вкладку в DevTools")
            print("   2. Данные могут быть в API endpoints - проверьте XHR запросы")
            print("   3. Попробуйте страницу: https://www.cbr.ru/statistics/credit_statistics/")
        else:
            print("   1. Используйте найденные таблицы/JS данные в парсере")
            print("   2. Реализуйте fallback на актуальные hardcoded данные")

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

    return True

if __name__ == "__main__":
    print("=" * 60)
    print("  ТЕСТИРОВАНИЕ ПАРСИНГА ДАННЫХ ЦБ РФ")
    print("=" * 60)

    success = test_cbr_scraping()

    print("\n" + "=" * 60)
    if success:
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
    else:
        print("❌ ОШИБКА В ТЕСТИРОВАНИИ")

    print("   Дата тестирования:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
