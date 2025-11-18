"""Models for patient presentation extraction."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PresentationData(BaseModel):
    symptoms: List[str] = Field(
        default_factory=list,
        description="Presenting symptoms or complaints documented at admission (normalized clinical terminology).",
    )
    symptom_source: Optional[str] = Field(
        default=None,
        description="Section where symptoms were documented (e.g., 'Chief Complaint', 'HPI').",
    )
    presentation_method: Optional[str] = Field(
        default=None,
        description="How the patient arrived: emergency_department, scheduled_admission, direct_admission, transfer, ambulance.",
    )
    presentation_details: Optional[str] = Field(
        default=None,
        description="Brief narrative (1-2 sentences) summarizing circumstances of presentation.",
    )
    presentation_timeline: Optional[str] = Field(
        default=None,
        description="Timeline of symptom onset or event (e.g., 'Symptoms began 2 hours ago', 'Fell this morning').",
    )
    severity_indicators: List[str] = Field(
        default_factory=list,
        description="Discrete acuity markers indicating urgency or instability (not duplicate of symptoms).",
    )


class PresentationExtractionResponse(BaseModel):
    patient_presentation: PresentationData
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


__all__ = ["PresentationData", "PresentationExtractionResponse"]

