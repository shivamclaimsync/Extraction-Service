"""Models for relevant history extraction."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..shared_models import MedicalCondition


class HistoryData(BaseModel):
    conditions: list[MedicalCondition] = Field(
        default_factory=list,
        description="List of pre-existing medical conditions or comorbidities.",
    )


class HistoryExtractionResponse(BaseModel):
    relevant_history: HistoryData
    patient_id: Optional[str] = Field(
        default=None,
        description="Patient identifier (extracted globally and shared across all extractions)."
    )
    hospitalization_id: Optional[str] = Field(
        default=None,
        description="Hospitalization identifier (extracted globally and shared across all extractions)."
    )

    def to_standardizer(self) -> dict:
        return self.model_dump()


__all__ = ["HistoryData", "HistoryExtractionResponse"]

