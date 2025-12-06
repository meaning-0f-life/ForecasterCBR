from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.llm.analyzer import LLMAnalyzer
from app.data.fetcher import DataFetcher
from app.data.cache import DataCache
from app.utils.logger import setup_logger
from app.webhook import router
import os
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)

app = FastAPI(title="CBR Key Rate Analysis MVP")
app.include_router(router)

# Initialize components
cache = DataCache(ttl=int(os.getenv("CACHE_TTL", 3600)))
fetcher = DataFetcher(
    news_api_key=os.getenv("NEWS_API_KEY", ""),
    economic_api_key=os.getenv("ECONOMIC_DATA_API_KEY", ""),
    cache=cache
)
analyzer = LLMAnalyzer(
    model=os.getenv("OLLAMA_MODEL", "llama2"),
    host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
)

class AnalysisRequest(BaseModel):
    custom_data: str = ""

@app.get("/")
def read_root():
    return {"message": "CBR Analysis System MVP", "version": "1.0.0"}

@app.post("/analyze")
def analyze_key_rate(request: AnalysisRequest):
    """Analyze the current CBR key rate."""
    try:
        data = request.custom_data or fetcher.get_combined_data()
        analysis = analyzer.analyze_key_rate(data_text=data)
        if not analysis:
            raise HTTPException(status_code=500, detail="Analysis failed")
        return {"analysis": analysis}
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/predict-change")
def predict_rate_change(request: AnalysisRequest):
    """Predict future rate changes (Russian)."""
    try:
        data = request.custom_data or fetcher.get_combined_data()
        prediction = analyzer.predict_rate_change(data_text=data)
        if not prediction:
            raise HTTPException(status_code=500, detail="Prediction failed")
        return {"prediction": prediction}
    except Exception as e:
        logger.error(f"Error in predict-change endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/predict-next-meeting")
def predict_next_meeting_rate(request: AnalysisRequest):
    """Predict key rate after next CBR meeting."""
    try:
        data = request.custom_data or fetcher.get_combined_data()
        meeting_data = fetcher.get_cbr_meeting_dates()

        next_date = meeting_data["next"]
        upcoming = meeting_data["upcoming"]
        past_rates = fetcher._fetch_cbr_key_rates_history()  # Get historical rates

        if not next_date:
            return {"error": "Нет запланированных заседаний ЦБ РФ"}

        prediction = analyzer.predict_next_meeting_rate(
            data_text=data,
            next_meeting_date=next_date,
            upcoming_dates=upcoming,
            historical_decisions=past_rates
        )
        if not prediction:
            raise HTTPException(status_code=500, detail="Next meeting prediction failed")

        return {
            "next_meeting_date": next_date,
            "prediction": prediction,
            "upcoming_dates": upcoming
        }
    except Exception as e:
        logger.error(f"Error in predict-next-meeting endpoint: {e}")
        raise HTTPException(status_code=500, detail="Prediction error")

@app.get("/meeting-dates")
def get_meeting_dates():
    """Get CBR meeting schedule."""
    try:
        dates = fetcher.get_cbr_meeting_dates()
        return dates
    except Exception as e:
        logger.error(f"Error fetching meeting dates: {e}")
        raise HTTPException(status_code=500, detail="Meeting dates fetch error")

@app.get("/data")
def get_data():
    """Get current data sources."""
    try:
        data = fetcher.get_combined_data()
        return {"data": data}
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise HTTPException(status_code=500, detail="Data fetch error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
