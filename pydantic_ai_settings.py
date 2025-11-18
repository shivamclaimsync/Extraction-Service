"""Configuration settings for Pydantic AI-based extraction system."""

from __future__ import annotations

from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env if present (helps CLI/demo usage)
load_dotenv()


class PydanticAISettings(BaseSettings):
    """Runtime settings for the Pydantic AI extraction pipeline."""

    model_name: str = Field(
        default="openai:gpt-4o-mini",
        description="Pydantic AI model identifier (e.g., 'openai:gpt-4o-mini', 'google-gla:gemini-2.0-flash').",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for the model provider. Defaults to OPENAI_API_KEY if unset.",
    )
    max_retries: int = Field(
        default=2,
        description="Maximum number of retry attempts on validation failure.",
        ge=0,
        le=5,
    )
    temperature: float = Field(
        default=0.0,
        description="Sampling temperature for LLM responses (0.0 = deterministic).",
        ge=0.0,
        le=2.0,
    )
    max_workers: int = Field(
        default=6,
        description="Maximum number of parallel extraction workers.",
        ge=1,
    )
    timeout_seconds: int = Field(
        default=180,
        description="Per-extraction timeout in seconds.",
        ge=30,
    )

    class Config:
        env_prefix = "PYDANTIC_AI_"


pydantic_ai_settings = PydanticAISettings()

if pydantic_ai_settings.api_key is None:
    # Fallback to standard environment variables.
    from os import getenv

    pydantic_ai_settings.api_key = getenv("OPENAI_API_KEY")

