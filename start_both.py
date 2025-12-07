#!/usr/bin/env python3
"""
Combined startup script for FastAPI server and Telegram bot.
Runs both concurrently using asyncio.
"""
import asyncio
import sys
import signal
import threading
from dotenv import load_dotenv
from app.main import app
from app.telegram_bot import init_telegram_bot, start_telegram_bot, stop_telegram_bot
from app.utils.logger import setup_logger
import uvicorn

load_dotenv()
logger = setup_logger(__name__)

async def run_fastapi():
    """Run FastAPI server with Uvicorn."""
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
    server = uvicorn.Server(config)

    await server.serve()

async def run_bot():
    """Run Telegram bot polling."""
    try:
        await start_telegram_bot()
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        raise

async def main():
    """Main function to run both FastAPI and bot concurrently."""
    logger.info("Starting CBR Analysis System with FastAPI + Telegram Bot...")

    # Initialize bot (only the instance, not polling)
    try:
        init_telegram_bot()
        logger.info("Telegram bot initialized successfully")
    except ValueError as e:
        logger.warning(f"Telegram bot initialization failed: {e}")
        logger.warning("Running FastAPI server without Telegram bot")
    except Exception as e:
        logger.error(f"Unexpected error initializing Telegram bot: {e}")
        logger.error("Running FastAPI server only")
        # Run FastAPI only
        await run_fastapi()
        return

    # Run both FastAPI and bot concurrently
    try:
        logger.info("Starting both FastAPI server and Telegram bot polling...")
        await asyncio.gather(
            run_fastapi(),
            run_bot(),
            return_exceptions=True
        )
    except Exception as e:
        logger.error(f"Error running both services: {e}")
    finally:
        logger.info("Stopping services...")
        await stop_telegram_bot()

if __name__ == "__main__":
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected shutdown: {e}")
        sys.exit(1)
