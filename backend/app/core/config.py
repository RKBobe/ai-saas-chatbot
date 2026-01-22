from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI SaaS Platform"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # <--- Added this
    
    # External Services
    OPENAI_API_KEY: str
    CHROMA_DB_URL: str = "http://localhost:8001"
    
    # Facebook Global Config
    FB_APP_ID: str                         # <--- Added this
    FB_APP_SECRET: str
    FB_VERIFY_TOKEN: str = "my_secure_random_token" 

    class Config:
        env_file = ".env"
        # This setting prevents the app from crashing if .env has extra variables
        extra = "ignore" 

settings = Settings()