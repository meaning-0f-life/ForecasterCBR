def test_data_fetching():
    """Test data fetching from economic sources"""
    from app.data.fetcher import DataFetcher
    from app.data.cache import DataCache
    import os
    from dotenv import load_dotenv

    load_dotenv()

    cache = DataCache(ttl=3600)
    fetcher = DataFetcher(
        news_api_key=os.getenv("NEWS_API_KEY", ""),
        economic_api_key=os.getenv("ECONOMIC_DATA_API_KEY", ""),
        cache=cache,
        telegram_api_id=int(os.getenv("TELEGRAM_API_ID", 0)) if os.getenv("TELEGRAM_API_ID") else None,
        telegram_api_hash=os.getenv("TELEGRAM_API_HASH", "")
    )

    print("=== ТЕСТИРОВАНИЕ ЗАГРУЗКИ ЭКОНОМИЧЕСКИХ ДАННЫХ ===")

    # Test inflation data fetching
    print("\n1. Тестирование загрузки данных по инфляции:")
    print("-" * 50)
    inflation_data = fetcher._fetch_inflation_history()
    print(inflation_data)

    # Test GDP data fetching
    print("\n2. Тестирование загрузки данных по ВВП:")
    print("-" * 50)
    gdp_data = fetcher._fetch_gdp_history()
    print(gdp_data)

    # Check if we got real API data or fallback
    print("\n3. АНАЛИЗ РЕЗУЛЬТАТОВ:")
    print("-" * 50)

    has_real_inflation = "ИНФЛЯЦИЯ Г/Г" in inflation_data and "World Bank API" in inflation_data
    has_real_gdp = "ВВП Г/Г" in gdp_data and "пример" not in gdp_data

    print(f"Реальные данные по инфляции: {'ДА' if has_real_inflation else 'НЕТ (используется пример)'}")
    print(f"Реальные данные по ВВП: {'ДА' if has_real_gdp else 'НЕТ (используется пример)'}")

    if not has_real_inflation:
        print("Внимание: Для получения реальных данных по инфляции нужно:")
        print("  - Настроить API ключ Alpha Vantage (ECONOMIC_DATA_API_KEY в .env)")
        print("  - Или добавить scraping с сайта ЦБ РФ/Росстата")

    if not has_real_gdp:
        print("Внимание: Для получения реальных данных по ВВП нужно:")
        print("  - Настроить API ключ Alpha Vantage (ECONOMIC_DATA_API_KEY в .env)")
        print("  - Или добавить scraping с сайта Росстата")

    return has_real_inflation or has_real_gdp

if __name__ == "__main__":
    from datetime import datetime
    print("=" * 60)
    print("  ТЕСТИРОВАНИЕ ЗАГРУЗКИ ЭКОНОМИЧЕСКИХ ДАННЫХ")
    print("=" * 60)

    success = test_data_fetching()

    print("\n" + "=" * 60)
    if success:
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО - есть данные")
    else:
        print("⚠️  ТЕСТИРОВАНИЕ ЗАВЕРШЕНО - используются примерные данные")

    print("   Время тестирования:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
