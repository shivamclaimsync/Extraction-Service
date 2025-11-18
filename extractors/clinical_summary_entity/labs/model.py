"""Models for laboratory results extraction."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..shared_models import LabSummary, LabTest


class LabExtractionResponse(BaseModel):
    lab_results: list[LabTest] = Field(default_factory=list)
    lab_summary: LabSummary = Field(default_factory=LabSummary)
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


__all__ = ["LabExtractionResponse"]

