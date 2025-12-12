# CBR Key Rate Analysis MVP

Минимальный Python проект, интегрирующий Telegram Bot с Ollama для анализа ключевой ставки Центрального банка РФ на основе актуальных новостей, экономических данных и научных статей. Анализ и прогнозы ведутся на русском языке в диалоговом режиме.

## Основные возможности

- **FastAPI сервер**: RESTful API для анализа ключевой ставки
- **Telegram Bot**: Прямое общение с пользователями без классификации intent'ов
- **Ollama LLM**: Использует локальные LLM модели для интеллектуального анализа на русском
- **Сбор данных**: Интеграция с телеграм каналом @centralbank_russia, экономическими данными и научными статьями
- **Исторические данные**: Доступ к историческим экономическим показателям и ставкам ЦБ РФ
- **Прогнозы заседаний**: Предсказание ставки после следующих заседаний ЦБ РФ
- **Кэширование**: TTL-основанное кэширование для эффективной работы
- **Контекстный анализ**: Ответы на любые вопросы с использованием полного контекста данных

## Project Structure

```
cbr-mvp-system/
├── README.md
├── requirements.txt
├── start_both.py ← Combined FastAPI + Telegram bot runner
├── docker-compose.yml
├── bot_runner.py ← Standalone Telegram bot runner (alternative)
├── .env
├── app/
│ ├── __init__.py
│ ├── main.py ← FastAPI server
│ ├── webhook.py ← Legacy Dialogflow webhook (deprecated)
│ ├── telegram_bot.py ← Telegram bot handler
│ ├── data/
│ │ ├── __init__.py
│ │ ├── fetcher.py ← API data fetching
│ │ └── cache.py ← Data caching
│ ├── llm/
│ │ ├── __init__.py
│ │ ├── analyzer.py ← Ollama queries
│ │ └── prompts.py ← Prompt templates
│ └── utils/
│ ├── __init__.py
│ └── logger.py ← Logging utility
└── tests/
 └── test_webhook.py
```

## Installation

1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`: `cp .env.example .env`
   - Edit `.env` file and add your API keys and tokens:
     - Новости теперь берутся из телеграм канала @centralbank_russia (дополнительная настройка не требуется)
     - Get Alpha Vantage API key from [alphavantage.co](https://www.alphavantage.co) для экономических данных
     - Create Telegram bot and get token from [@BotFather](https://t.me/BotFather)
     - Optionally configure DeepSeek API key

4. Ensure Ollama is running locally with the specified model:
   ```bash
   ollama pull llama3.2:1b  # or your chosen model
   ```

## Telegram Bot Setup

1. Создайте бота через @BotFather в Telegram
2. Скопируйте токен бота
3. Добавьте токен в `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

## Running

### Option 1: Combined FastAPI + Telegram Bot (Development)
```bash
# Start both server and bot together
python start_both.py
```

### Option 2: Separate Processes (Production/Testing)
```bash
# Terminal 1: FastAPI server only
python -m app.main

# Terminal 2: Telegram bot only
python bot_runner.py
```

### Option 3: Production with Docker
```bash
# Build and run
docker-compose up --build
```

## API Endpoints

- `GET /`: Проверка работоспособности
- `POST /analyze`: Анализ текущей ключевой ставки
- `POST /predict-change`: Прогноз изменения ставки
- `POST /predict-next-meeting`: Прогноз ставки после следующего заседания ЦБ РФ
- `GET /meeting-dates`: Получить даты заседаний ЦБ РФ
- `GET /data`: Получить текущие данные для анализа

## Научные статьи

Для улучшения контекста анализа загрузите научные статьи в папку `articles/` (рядом с requirements.txt):
- Источники для статей: cbr.ru (отчеты по инфляции), imf.org, worldbank.org, academic databases (Google Scholar, RePEc, SSRN)
- Формат: .txt файлы в кодировке UTF-8
- Система автоматически включит их в анализ
- Подробности см. в articles/README.md

## DeepSeek Cloud Model Support

Система теперь поддерживает как локальные модели Ollama, так и облачные модели DeepSeek!

### Настройка DeepSeek:

1. **Зарегистрируйтесь** на [platform.deepseek.com](https://platform.deepseek.com)
2. **Получите API ключ** в личном кабинете
3. **Настройте переменные в .env**:
   ```bash
   # Включить DeepSeek вместо Ollama
   USE_DEEPSEEK=true

   # API данные DeepSeek
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
   DEEPSEEK_MODEL=deepseek-chat  # или deepseek-coder
   ```

### Преимущества DeepSeek:

- **Быстрая работа** - не нужно локальное оборудование
- **Масштабируемость** - обработка большого числа запросов
- **Качество ответов** - современная архитектура модели
- **Автоматическое переключение** - fallback на Ollama если DeepSeek недоступен

### Переключение между провайдерами:

```bash
# Для локального Ollama
USE_DEEPSEEK=false
OLLAMA_MODEL=llama3.2:1b

# Для DeepSeek Cloud
USE_DEEPSEEK=true
DEEPSEEK_MODEL=deepseek-chat
```

## Особенности работы с Telegram ботом

- **Эффективная архитектура**: Системный контекст обновляется автоматически каждые CACHE_TTL секунд (настройка в .env)
- **Быстрые ответы**: Бот использует предзагруженный контекст, а не получает данные каждый раз
- **Любые вопросы**: Нет классификации intent'ов - отвечаем на любые вопросы о ЦБ РФ, экономике, ставках
- **Полный анализ**: Ответы основаны на: новостях, заседаниях ЦБ, истории ставок, инфляции, ВВП
- **Автоматические обновления**: Контекст обновляется в фоне каждые 3600 секунд (по умолчанию)
- **Поддержка команд**: /start и /help для помощи пользователям

## Environment Variables

See `.env` file for required configuration.

## Testing

Run pytest tests:
```bash
python -m pytest tests/
```

### CBR Data Scraping Test

Test the CBR.ru key rate parsing functionality:
```bash
python test_cbr_scraping.py
```

This will analyze the CBR website structure and provide recommendations for implementing real-time data parsing.

## License

This is an MVP implementation. Use at your own risk.
