import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    GEMINI_API_KEY: str
    GITHUB_TOKEN: str
    DATABASE_URL: str
    
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str | None = "ai-chat-modular"
    
    # Base directory of the workspace
    BASE_DIR: str = str(Path(__file__).resolve().parent.parent.parent)

# Initialize settings
settings = Settings()

# Automatically load LangSmith environment variables if tracing is enabled
if settings.LANGCHAIN_TRACING_V2.lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    if settings.LANGCHAIN_PROJECT:
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

# Automatically load Gemini/Google key into standard environment variables
os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY
