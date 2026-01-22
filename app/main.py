from fastapi import FastAPI
from app.utils.logger import setup_logger
import os
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)

app = FastAPI(title="CBR Key Rate Analysis MVP")



@app.get("/")
def read_root():
    return {"message": "CBR Analysis System MVP", "version": "1.0.0", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
