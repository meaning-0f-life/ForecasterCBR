from fastapi import APIRouter, Request
from app.utils.logger import setup_logger

# DEPRECATED: This module was used for Dialogflow integration.
# The system now uses direct Telegram bot integration instead.
# This webhook is kept for backward compatibility but is not used.

logger = setup_logger(__name__)

router = APIRouter()

@router.post("/dialogflow-webhook")
async def dialogflow_webhook(request: Request):
    """DEPRECATED: Dialogflow webhook - no longer used. Use Telegram bot instead."""
    logger.warning("Dialogflow webhook called - this endpoint is deprecated")
    return {"message": "Dialogflow integration deprecated. Use Telegram bot instead.", "deprecated": True}
