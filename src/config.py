"""
Модуль конфигурации приложения
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Конфигурация приложения"""
    
    def __init__(self):
        # Загружаем переменные окружения из .env файла
        load_dotenv()
        
        self.zvuk_api_token = os.getenv("ZVUK_API_TOKEN")
        self.local_library_path = os.getenv("LOCAL_LIBRARY_PATH")
        
        # Валидация
        if not self.zvuk_api_token:
            raise ValueError("ZVUK_API_TOKEN не найден в переменных окружения")
        
        if not self.local_library_path:
            raise ValueError("LOCAL_LIBRARY_PATH не найден в переменных окружения")
        
        self.library_path = Path(self.local_library_path)
        
        if not self.library_path.exists():
            raise ValueError(f"Путь к библиотеке не существует: {self.library_path}")
    
    @property
    def api_headers(self) -> dict:
        """Заголовки для API запросов"""
        return {
            "Authorization": f"Bearer {self.zvuk_api_token}",
            "Content-Type": "application/json"
        }
