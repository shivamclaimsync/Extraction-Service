"""Medication risk assessment extraction tool."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from pydantic_ai.agent import Agent
from pydantic_ai.exceptions import ModelRetry, UnexpectedModelBehavior

from pydantic_ai_settings import pydantic_ai_settings

from .model import MedicationRiskExtractionResponse
from .prompts import medication_risk_prompt, system_prompt

logger = logging.getLogger(__name__)


def build_medication_risk_agent(
    model_name: Optional[str] = None,
    system_prompt_override: Optional[str] = None,
) -> Agent[None, MedicationRiskExtractionResponse]:
    """Create a configured Pydantic AI agent for medication risk assessment."""
    return Agent(
        model=model_name or pydantic_ai_settings.model_name,
        output_type=MedicationRiskExtractionResponse,
        system_prompt=system_prompt_override or system_prompt,
        retries=pydantic_ai_settings.max_retries,
    )


@dataclass
class MedicationRiskPydanticAITool:
    """Run medication risk assessment using a Pydantic AI Agent."""

    model_name: Optional[str] = None
    system_prompt_override: Optional[str] = None

    def __post_init__(self) -> None:
        if not pydantic_ai_settings.api_key:
            raise RuntimeError(
                "OpenAI API key not configured. Set PYDANTIC_AI_API_KEY or OPENAI_API_KEY."
            )
        self._agent = build_medication_risk_agent(
            model_name=self.model_name,
            system_prompt_override=self.system_prompt_override,
        )

    async def run(self, clinical_text: str) -> MedicationRiskExtractionResponse:
        """Execute extraction and return a validated response payload."""
        prompt = medication_risk_prompt.format(clinical_text=clinical_text)
        try:
            result = await self._agent.run(prompt)
            return result.output
        except ModelRetry as exc:
            logger.error("Medication risk assessment retries exhausted: %s", exc)
            raise ValueError(
                "Medication risk assessment failed to produce schema-compliant output."
            ) from exc
        except UnexpectedModelBehavior as exc:
            logger.error("Unexpected model behavior in medication risk assessment: %s", exc)
            raise ValueError(
                "Medication risk assessment encountered unexpected model behavior."
            ) from exc
        except Exception as exc:
            logger.error("Medication risk assessment failed: %s", exc)
            raise ValueError(f"Medication risk assessment failed: {exc}") from exc


__all__ = ["MedicationRiskPydanticAITool", "build_medication_risk_agent"]

