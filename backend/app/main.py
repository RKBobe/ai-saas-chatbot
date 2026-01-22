from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
# FIX 1: Changed 'vi' to 'v1'
from app.api.v1.endpoints import webhooks 
from app.db.base import Base
from app.db.session import engine

# --- 1. Database Setup ---
#FIX: Import models here so sqlalchemy knows about them
from app.models.user import User
from app.models.chatbot import Chatbot

Base.metadata.create_all(bind=engine)

# --- 2. App Initialization ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- 3. CORS Configuration ---
# FIX 2: Defined 'origins' so the middleware can use it
origins = [
    "http://localhost:5173",  # Vite default port
    "http://localhost:3000",  # Create React App default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. Include Routers ---
app.include_router(
    webhooks.router, 
    prefix=f"{settings.API_V1_STR}/webhooks", 
    tags=["Webhooks"]
)

# --- 5. Health Check ---
@app.get("/")
def read_root():
    return {"status": "active", "message": "AI SaaS Backend is running"}