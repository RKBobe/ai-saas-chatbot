from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI SaaS Platform"
    API_V1_STR: str = "/api/v1"
    
    # --- Security & Network ---
    # This was the missing piece causing the crash:
    BACKEND_CORS_ORIGINS: List[str] = ["*"] 
    
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # --- Database ---
    DATABASE_URL: str
    CHROMA_DB_URL: str
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    
    # --- Facebook Integration ---
    FB_APP_ID: str = ""
    FB_APP_SECRET: str = ""
    FB_VERIFY_TOKEN: str = ""
    FB_PAGE_ACCESS_TOKEN: str = ""
    
    # --- AI Providers ---
    OPENAI_API_KEY: str = "" 
    GEMINI_API_KEY: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()