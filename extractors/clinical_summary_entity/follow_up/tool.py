"""Follow-up plan extraction tool."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from pydantic_ai.agent import Agent
from pydantic_ai.exceptions import ModelRetry, UnexpectedModelBehavior

try:
    from new.pydantic_ai_settings import pydantic_ai_settings
except ImportError:
    from extraction_service.pydantic_ai_settings import pydantic_ai_settings
from .model import FollowUpExtractionResponse
from .prompts import follow_up_prompt, system_prompt

logger = logging.getLogger(__name__)


def build_follow_up_agent(
    model_name: Optional[str] = None,
    system_prompt_override: Optional[str] = None,
) -> Agent[None, FollowUpExtractionResponse]:
    return Agent(
        model=model_name or pydantic_ai_settings.model_name,
        output_type=FollowUpExtractionResponse,
        system_prompt=system_prompt_override or system_prompt,
        retries=pydantic_ai_settings.max_retries,
    )


@dataclass
class FollowUpPydanticAITool:
    model_name: Optional[str] = None
    system_prompt_override: Optional[str] = None

    def __post_init__(self) -> None:
        if not pydantic_ai_settings.api_key:
            raise RuntimeError(
                "OpenAI API key not configured. Set PYDANTIC_AI_API_KEY or OPENAI_API_KEY."
            )
        self._agent = build_follow_up_agent(
            model_name=self.model_name,
            system_prompt_override=self.system_prompt_override,
        )

    async def run(self, clinical_text: str) -> FollowUpExtractionResponse:
        prompt = follow_up_prompt.format(clinical_text=clinical_text)
        try:
            result = await self._agent.run(prompt)
            return result.output
        except ModelRetry as exc:
            logger.error("Follow-up plan extraction retries exhausted: %s", exc)
            raise ValueError(
                "Follow-up plan extraction failed to produce schema-compliant output."
            ) from exc
        except UnexpectedModelBehavior as exc:
            logger.error("Unexpected model behavior in follow-up extraction: %s", exc)
            raise ValueError("Follow-up plan extraction encountered unexpected model behavior.") from exc
        except Exception as exc:
            logger.error("Follow-up plan extraction failed: %s", exc)
            raise ValueError(f"Follow-up plan extraction failed: {exc}") from exc

