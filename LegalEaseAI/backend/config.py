from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    app_name: str = Field(
        default_factory=lambda: os.getenv(
            "APP_NAME",
            "LegalEase"
        )
    )

    company_name: str = Field(
        default_factory=lambda: os.getenv(
            "COMPANY_NAME",
            "LegalEase"
        )
    )

    gemini_api_key: str | None = Field(
        default_factory=lambda: os.getenv(
            "GEMINI_API_KEY"
        )
    )

    gemini_model: str = Field(
        default_factory=lambda: os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash"
        )
    )

    demo_mode: bool = Field(
        default_factory=lambda:
        os.getenv(
            "DEMO_MODE",
            "false"
        ).lower() == "true"
    )

    backend_url: str = Field(
        default_factory=lambda: os.getenv(
            "BACKEND_URL",
            "http://127.0.0.1:8000"
        )
    )

    font_name: str = Field(
        default_factory=lambda: os.getenv(
            "FONT_NAME",
            "Times New Roman"
        )
    )

    logo_path: str = Field(
        default_factory=lambda: str(
            BASE_DIR
            / "assets"
            / "legalese_logo.png"
        )
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()