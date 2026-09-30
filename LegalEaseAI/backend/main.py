from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.routes import router


settings = get_settings()


app = FastAPI(
    title=(
        "LegalEase - AI Legal "
        "Document Generator API"
    ),
    version="1.0.0",
    description=(
        "Backend API for generating "
        "editable legal-document drafts."
    )
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS"
    ],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/", tags=["health"])
def root():

    return {
        "message": (
            "Welcome to LegalEase AI "
            "Legal Document Generator API"
        ),
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["health"])
def health():

    return {
        "status": "ok",
        "app": settings.app_name,
        "demo_mode": settings.demo_mode,
        "gemini_configured": bool(
            settings.gemini_api_key
        )
    }