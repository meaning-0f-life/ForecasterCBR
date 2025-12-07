#!/usr/bin/env python3
"""
Standalone script to run the Telegram bot alongside FastAPI server.
This provides a separate process for the bot polling.
"""
import asyncio
import signal
import sys
from dotenv import load_dotenv
from app.telegram_bot import init_telegram_bot, start_telegram_bot, stop_telegram_bot
from app.utils.logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)

async def main():
    """Main function to run the Telegram bot."""
    try:
        logger.info("Initializing Telegram bot...")
        init_telegram_bot()

        logger.info("Starting bot polling...")
        await start_telegram_bot()

    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)
    finally:
        logger.info("Stopping bot...")
        await stop_telegram_bot()

if __name__ == "__main__":
    asyncio.run(main())
