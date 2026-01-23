from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI SaaS Platform"
    API_V1_STR: str = "/api/v1"
    
    # This was missing:
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External Services
    OPENAI_API_KEY: str
    CHROMA_DB_URL: str = "http://localhost:8001"
    
    # Facebook Global Config
    FB_APP_ID: str
    FB_APP_SECRET: str
    FB_VERIFY_TOKEN: str = "MY_SECURE_rANDOM_TOKEN" 
    FB_PAGE_ACCESS_TOKEN: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore" 

settings = Settings()