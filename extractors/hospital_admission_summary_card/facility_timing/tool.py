"""Facility and timing extraction tool."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from pydantic_ai.agent import Agent
from pydantic_ai.exceptions import ModelRetry, UnexpectedModelBehavior

from pydantic_ai_settings import pydantic_ai_settings

from .model import FacilityTimingExtractionResponse
from .prompts import facility_timing_prompt, system_prompt

logger = logging.getLogger(__name__)


def build_facility_timing_agent(
    model_name: Optional[str] = None,
    system_prompt_override: Optional[str] = None,
) -> Agent[None, FacilityTimingExtractionResponse]:
    """Create a configured Pydantic AI agent for facility and timing extraction."""
    return Agent(
        model=model_name or pydantic_ai_settings.model_name,
        output_type=FacilityTimingExtractionResponse,
        system_prompt=system_prompt_override or system_prompt,
        retries=pydantic_ai_settings.max_retries,
    )


@dataclass
class FacilityTimingPydanticAITool:
    """Run facility and timing extraction using a Pydantic AI Agent."""

    model_name: Optional[str] = None
    system_prompt_override: Optional[str] = None

    def __post_init__(self) -> None:
        if not pydantic_ai_settings.api_key:
            raise RuntimeError(
                "OpenAI API key not configured. Set PYDANTIC_AI_API_KEY or OPENAI_API_KEY."
            )
        self._agent = build_facility_timing_agent(
            model_name=self.model_name,
            system_prompt_override=self.system_prompt_override,
        )

    async def run(self, clinical_text: str) -> FacilityTimingExtractionResponse:
        """Execute extraction and return a validated response payload."""
        prompt = facility_timing_prompt.format(clinical_text=clinical_text)
        try:
            result = await self._agent.run(prompt)
            return result.output
        except ModelRetry as exc:
            logger.error("Facility/timing extraction retries exhausted: %s", exc)
            raise ValueError(
                "Facility and timing extraction failed to produce schema-compliant output."
            ) from exc
        except UnexpectedModelBehavior as exc:
            logger.error("Unexpected model behavior in facility/timing extraction: %s", exc)
            raise ValueError(
                "Facility and timing extraction encountered unexpected model behavior."
            ) from exc
        except Exception as exc:
            logger.error("Facility/timing extraction failed: %s", exc)
            raise ValueError(f"Facility and timing extraction failed: {exc}") from exc


__all__ = ["FacilityTimingPydanticAITool", "build_facility_timing_agent"]

