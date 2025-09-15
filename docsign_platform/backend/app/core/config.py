import os
from pydantic_settings import BaseSettings
from typing import List, Union

# Get the base directory of the backend project
# This ensures that the .env file is found correctly regardless of where the script is run from
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocSign Platform API"
    API_V1_STR: str = "/api/v1"

    # Database URL
    DATABASE_URL: str

    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Storage Path
    STORAGE_BASE_PATH: str = os.path.join(BASE_DIR, "backend/storage")

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    class Config:
        # Pydantic will read variables from this file
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = 'utf-8'
        case_sensitive = True

# Create a single instance of the settings to be imported in other modules
settings = Settings()