from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import webhooks, chat, inventory, appointments, sms, voice, documents
from app.db.base import Base
from app.db.session import engine

# Explicitly import models to register with metadata
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.inventory import Inventory
from app.models.appointment import Appointment
from app.models.conversation import Conversation

# Auto-create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include the Webhook Router
app.include_router(
    webhooks.router, 
    prefix=f"{settings.API_V1_STR}/webhooks", 
    tags=["webhooks"]
)

# Include Generic Chat Router
app.include_router(
    chat.router, 
    prefix=f"{settings.API_V1_STR}/chat", 
    tags=["chat"]
)

# Include Inventory Router
app.include_router(
    inventory.router,
    prefix=f"{settings.API_V1_STR}/inventory",
    tags=["inventory"]
)

# Include Appointments Router
app.include_router(
    appointments.router,
    prefix=f"{settings.API_V1_STR}/appointments",
    tags=["appointments"]
)

# Include SMS Router
app.include_router(
    sms.router,
    prefix=f"{settings.API_V1_STR}/sms",
    tags=["sms"]
)

# Include Voice Router
app.include_router(
    voice.router,
    prefix=f"{settings.API_V1_STR}/voice",
    tags=["voice"]
)

# Include Documents Router
app.include_router(
    documents.router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["documents"]
)

@app.get("/")
def root():
    return {"message": "Welcome to the AI SaaS API"}