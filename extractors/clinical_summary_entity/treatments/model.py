"""Models for treatments and procedures extraction."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from ..shared_models import MedicationTreatment, ProcedureDetails, Treatment


class TreatmentsExtractionResponse(BaseModel):
    treatments_procedures: List[Treatment] = Field(default_factory=list)
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


__all__ = ["TreatmentsExtractionResponse", "Treatment", "MedicationTreatment", "ProcedureDetails"]

