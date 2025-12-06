# CBR Key Rate Analysis MVP

Минимальный Python проект, интегрирующий Dialogflow с Ollama для анализа ключевой ставки Центрального банка РФ на основе актуальных новостей, экономических данных и научных статей. Анализ и прогнозы ведутся на русском языке.

## Основные возможности

- **FastAPI сервер**: RESTful API для анализа ключевой ставки
- **Интеграция с Dialogflow**: Вебхук для разговорного ИИ с поддержкой русского языка
- **Ollama LLM**: Использует локальные LLM модели для интеллектуального анализа на русском
- **Сбор данных**: Интеграция с новостными API, экономическими данными и научными статьями
- **Исторические данные**: Доступ к историческим экономическим показателям и ставкам ЦБ РФ
- **Прогнозы заседаний**: Предсказание ставки после следующих заседаний ЦБ РФ
- **Кэширование**: TTL-основанное кэширование для эффективной работы

## Project Structure

```
cbr-mvp-system/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── .env
├── app/
│ ├── __init__.py
│ ├── main.py ← FastAPI server
│ ├── webhook.py ← Dialogflow webhook handler
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

3. Set up environment variables in `.env`:
   - Configure your API keys for news and economic data
   - Set Ollama host and model
   - Adjust Dialogflow settings if needed

4. Ensure Ollama is running locally with the specified model:
   ```bash
   ollama pull llama2  # or your chosen model
   ```

## Running

### Development Server
```bash
python -m app.main
```

### Production with Docker
```bash
docker-compose up --build
```

## API Endpoints

- `GET /`: Проверка работоспособности
- `POST /analyze`: Анализ текущей ключевой ставки
- `POST /predict-change`: Прогноз изменения ставки
- `POST /predict-next-meeting`: Прогноз ставки после следующего заседания ЦБ РФ
- `GET /meeting-dates`: Получить даты заседаний ЦБ РФ
- `GET /data`: Получить текущие данные для анализа
- `POST /dialogflow-webhook`: Вебхук Dialogflow

## Научные статьи

Для улучшения контекста анализа загрузите научные статьи в папку `articles/` (рядом с requirements.txt):
- Источники для статей: cbr.ru (отчеты по инфляции), imf.org, worldbank.org, academic databases (Google Scholar, RePEc, SSRN)
- Формат: .txt файлы в кодировке UTF-8
- Система автоматически включит их в анализ
- Подробности см. в articles/README.md

## Dialogflow Setup

1. Create a Dialogflow agent
2. Define intents:
   - `AnalyzeKeyRate` - анализ ключевой ставки
   - `PredictRateChange` - прогноз изменения ставки
   - `PredictNextMeeting` - прогноз после следующего заседания
   - `GetCurrentData` - получить текущие данные
   - `GetMeetingDates` - даты заседаний ЦБ РФ
3. Set webhook URL to point to `/dialogflow-webhook`
4. Enable webhook fulfillment for the intents

## Environment Variables

See `.env` file for required configuration.

## Testing

Run tests:
```bash
python -m pytest tests/
```

## License

This is an MVP implementation. Use at your own risk.
