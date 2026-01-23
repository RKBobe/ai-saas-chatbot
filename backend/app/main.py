from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import webhooks

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
# This connects the "webhooks.py" file to the "/api/v1/webhooks" URL
app.include_router(
    webhooks.router, 
    prefix=f"{settings.API_V1_STR}/webhooks", 
    tags=["webhooks"]
)

@app.get("/")
def root():
    return {"message": "Welcome to the AI SaaS API"}