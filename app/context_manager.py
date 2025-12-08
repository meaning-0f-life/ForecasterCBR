import threading
import time
import os
from datetime import datetime, timedelta
from app.data.fetcher import DataFetcher
from app.data.cache import DataCache
from app.utils.logger import setup_logger
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)

class SystemContextManager:
    """
    Менеджер системного контекста для LLM.
    Обновляет контекст каждые CACHE_TTL секунд автоматически.
    """

    def __init__(self):
        self.cache = DataCache(ttl=int(os.getenv("CACHE_TTL", 3600)))
        self.fetcher = DataFetcher(
            news_api_key=os.getenv("NEWS_API_KEY", ""),
            economic_api_key=os.getenv("ECONOMIC_DATA_API_KEY", ""),
            cache=self.cache
        )

        self.system_context = ""
        self.last_update = None
        self.update_interval = int(os.getenv("CACHE_TTL", 3600))  # секунды

        # Обновляем контекст при инициализации
        self._update_context()

        # Запускаем автоматическое обновление в фоне
        self._start_auto_update_thread()

    def _start_auto_update_thread(self):
        """Запускаем поток для автоматического обновления контекста."""
        def update_loop():
            while True:
                time.sleep(self.update_interval)
                try:
                    logger.info("Auto-updating system context...")
                    self._update_context()
                    logger.info("System context updated successfully")
                except Exception as e:
                    logger.error(f"Failed to auto-update context: {e}")

        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        logger.info(f"Started auto-update thread (interval: {self.update_interval}s)")

    def _update_context(self):
        """Обновляем системный контекст свежими данными."""
        try:
            # Получаем все данные
            news_articles = self.fetcher.get_combined_data()

            # Форматируем системный контекст
            context_parts = []

            # Текущая дата и время
            current_datetime_info = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (МСК, UTC+3)"
            context_parts.append(f"=== ТЕКУЩАЯ ДАТА И ВРЕМЯ ===\n{current_datetime_info}")

            # Новости и статьи (уже содержит экономические данные)
            context_parts.append(f"=== НОВОСТИ И ЭКОНОМИЧЕСКИЕ ДАННЫЕ ===\n{news_articles}")

            # Обновляем контекст
            self.system_context = "\n\n".join(context_parts)
            self.last_update = datetime.now()

            logger.info(f"System context updated at {self.last_update}")

        except Exception as e:
            logger.error(f"Error updating system context: {e}")
            # Если обновление не удалось, оставляем старый контекст

    def get_context(self, force_update: bool = False) -> str:
        """Получить актуальный системный контекст."""
        if force_update or self._needs_update():
            self._update_context()

        return self.system_context

    def _needs_update(self) -> bool:
        """Проверить, нужно ли обновлять контекст."""
        if self.last_update is None:
            return True

        time_passed = datetime.now() - self.last_update
        return time_passed.total_seconds() >= self.update_interval

    def force_update(self):
        """Принудительно обновить контекст."""
        logger.info("Forced context update requested")
        self._update_context()

# Глобальный экземпляр
context_manager = None

def get_context_manager():
    """Получить глобальный менеджер контекста."""
    global context_manager
    if context_manager is None:
        context_manager = SystemContextManager()
    return context_manager
