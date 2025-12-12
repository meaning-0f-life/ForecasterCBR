#!/usr/bin/env python3
"""
Скрипт для предварительной загрузки данных из Telegram канала @centralbank_russia
Запускать отдельно перед запуском основного приложения
"""

import sys
import os
import asyncio
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data.fetcher import DataFetcher
from app.data.cache import DataCache
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🔄 Предварительная загрузка данных из Telegram канала @centralbank_russia...")

    try:
        # Создаем fetcher с правильными credentials
        cache = DataCache(ttl=3600)  # 1 час TTL
        fetcher = DataFetcher(
            news_api_key=os.getenv('NEWS_API_KEY', ''),
            economic_api_key=os.getenv('ECONOMIC_DATA_API_KEY', ''),
            cache=cache,
            telegram_api_id=int(os.getenv('TELEGRAM_API_ID', 0)) if os.getenv('TELEGRAM_API_ID') else None,
            telegram_api_hash=os.getenv('TELEGRAM_API_HASH', '')
        )

        # Проверяем credentials
        if not fetcher.telegram_api_id or not fetcher.telegram_api_hash:
            print("❌ Ошибка: TELEGRAM_API_ID или TELEGRAM_API_HASH не установлены в .env")
            return False

        # Загружаем Telegram данные
        print("📡 Загружаем посты из @centralbank_russia...")
        result = fetcher._fetch_news_from_telegram()

        if result and "centralbank_russia" in result:
            print("✅ Успешно! Посты из @centralbank_russia сохранены в кэш")
            print("📊 Статистика:")

            # Выводим краткую статистику
            lines = result.split('\n')
            news_lines = [line for line in lines if line.startswith('- ') and '|' in line]
            print(f"   • Загружено постов: {len(news_lines)}")
            print(f"   • Данные кэшированы на 1 час")
            print(f"   • Время обновления: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Показываем пример первых 2 постов
            if news_lines:
                print("\n📝 Примеры загруженных постов:")
                for i, line in enumerate(news_lines[:2]):
                    # Сокращаем длинные посты для вывода
                    if len(line) > 150:
                        line = line[:147] + "..."
                    print(f"   {i+1}. {line}")

            return True
        else:
            print("❌ Ошибка загрузки данных из Telegram")
            print("Подробности результата:", result[:200] if result else "None")
            return False

    except Exception as e:
        print(f"❌ Кritical ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Готово! Теперь при запуске приложения в промпте будут посты из @centralbank_russia")
        print("💡 Совет: Запускайте этот скрипт каждый час для обновления данных")
    else:
        print("\n🚫 Что-то пошло не так. Проверьте настройки и повторите.")
        sys.exit(1)
