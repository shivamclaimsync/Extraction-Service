"""Models for diagnosis data extraction."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SecondaryDiagnosis(BaseModel):
    diagnosis: str = Field(
        description="Secondary diagnosis name (exact wording from clinical note)."
    )
    icd10_code: Optional[str] = Field(
        default=None,
        description="ICD-10 code for the secondary diagnosis ONLY if explicitly documented.",
    )
    evidence: str = Field(
        description="Section name and direct quote from the note where this diagnosis was found."
    )
    relationship_to_primary: Optional[str] = Field(
        default=None,
        description="Relationship to primary diagnosis: 'complication of', 'contributing factor', 'pre-existing condition', 'unrelated', or null.",
    )


class DiagnosisData(BaseModel):
    primary_diagnosis: str = Field(
        description="Primary diagnosis or reason for admission (exact wording from clinical note)."
    )
    primary_diagnosis_icd10: Optional[str] = Field(
        default=None,
        description="ICD-10 code for the primary diagnosis ONLY if explicitly documented in the note.",
    )
    primary_diagnosis_evidence: str = Field(
        description="Section name and direct quote from the note where the primary diagnosis was found."
    )
    diagnosis_category: str = Field(
        description="Clinical category of the primary diagnosis: cardiovascular, renal, respiratory, neurological, gastrointestinal, endocrine, infectious, musculoskeletal, psychiatric, trauma, environmental, or other.",
    )
    secondary_diagnoses: List[SecondaryDiagnosis] = Field(
        default_factory=list,
        description="List of secondary diagnoses that are actively managed or relevant to this encounter (not entire past medical history).",
    )


class DiagnosisExtractionResponse(BaseModel):
    diagnosis: DiagnosisData

    def to_standardizer(self) -> dict:
        return self.model_dump()


__all__ = [
    "SecondaryDiagnosis",
    "DiagnosisData",
    "DiagnosisExtractionResponse",
]

