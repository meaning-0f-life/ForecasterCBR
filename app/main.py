from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.utils.logger import setup_logger
from app.webhook import router
import os
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)

app = FastAPI(title="CBR Key Rate Analysis MVP")
app.include_router(router)



@app.get("/")
def read_root():
    return {"message": "CBR Analysis System MVP", "version": "1.0.0", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
