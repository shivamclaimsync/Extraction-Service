"""Diagnosis extraction tool."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from pydantic_ai.agent import Agent
from pydantic_ai.exceptions import ModelRetry, UnexpectedModelBehavior

from extraction_service.pydantic_ai_settings import pydantic_ai_settings

from .model import DiagnosisExtractionResponse
from .prompts import diagnosis_prompt, system_prompt

logger = logging.getLogger(__name__)


def build_diagnosis_agent(
    model_name: Optional[str] = None,
    system_prompt_override: Optional[str] = None,
) -> Agent[None, DiagnosisExtractionResponse]:
    """Create a configured Pydantic AI agent for diagnosis extraction."""
    return Agent(
        model=model_name or pydantic_ai_settings.model_name,
        output_type=DiagnosisExtractionResponse,
        system_prompt=system_prompt_override or system_prompt,
        retries=pydantic_ai_settings.max_retries,
    )


@dataclass
class DiagnosisPydanticAITool:
    """Run diagnosis extraction using a Pydantic AI Agent."""

    model_name: Optional[str] = None
    system_prompt_override: Optional[str] = None

    def __post_init__(self) -> None:
        if not pydantic_ai_settings.api_key:
            raise RuntimeError(
                "OpenAI API key not configured. Set PYDANTIC_AI_API_KEY or OPENAI_API_KEY."
            )
        self._agent = build_diagnosis_agent(
            model_name=self.model_name,
            system_prompt_override=self.system_prompt_override,
        )

    async def run(self, clinical_text: str) -> DiagnosisExtractionResponse:
        """Execute extraction and return a validated response payload."""
        prompt = diagnosis_prompt.format(clinical_text=clinical_text)
        try:
            result = await self._agent.run(prompt)
            return result.output
        except ModelRetry as exc:
            logger.error("Diagnosis extraction retries exhausted: %s", exc)
            raise ValueError(
                "Diagnosis extraction failed to produce schema-compliant output."
            ) from exc
        except UnexpectedModelBehavior as exc:
            logger.error("Unexpected model behavior in diagnosis extraction: %s", exc)
            raise ValueError(
                "Diagnosis extraction encountered unexpected model behavior."
            ) from exc
        except Exception as exc:
            logger.error("Diagnosis extraction failed: %s", exc)
            raise ValueError(f"Diagnosis extraction failed: {exc}") from exc


__all__ = ["DiagnosisPydanticAITool", "build_diagnosis_agent"]

