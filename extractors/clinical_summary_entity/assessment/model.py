"""Models for clinical assessment extraction."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MedicationRelationshipConfidence(str, Enum):
    definite = "definite"
    probable = "probable"
    possible = "possible"


class MedicationRelationship(BaseModel):
    implicated_medications: List[str] = Field(
        default_factory=list,
        description="List of medications implicated in the clinical presentation.",
    )
    mechanism: Optional[str] = Field(
        default=None,
        description="Mechanism by which medications contributed to the presentation.",
    )
    mechanism_evidence: Optional[str] = Field(
        default=None,
        description="Section name and direct quote supporting the mechanism.",
    )
    confidence: MedicationRelationshipConfidence = Field(
        description="Level of confidence in medication relationship."
    )
    confidence_rationale: Optional[str] = Field(
        default=None,
        description="Explanation of why this confidence level was assigned.",
    )
    temporal_relationship: Optional[str] = Field(
        default=None,
        description="Timeline of medication use relative to symptom onset.",
    )
    additional_factors: List[str] = Field(
        default_factory=list,
        description="Contextual factors supporting the medication link (e.g., baseline hypoxemia).",
    )


class CauseDeterminationConfidence(str, Enum):
    definite = "definite"
    probable = "probable"
    possible = "possible"
    uncertain = "uncertain"


class CauseDetermination(BaseModel):
    cause: str = Field(
        description="Identified precipitating cause of the presentation.",
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="List of evidence points supporting this cause determination.",
    )
    evidence_source: Optional[str] = Field(
        default=None,
        description="Section name where cause determination was documented.",
    )
    confidence: CauseDeterminationConfidence = Field(
        default=CauseDeterminationConfidence.probable,
        description="Level of confidence in the cause determination.",
    )


class FallRiskLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


class FallRiskAssessment(BaseModel):
    risk_level: FallRiskLevel
    contributing_factors: List[str] = Field(default_factory=list)


class AssessmentData(BaseModel):
    primary_diagnosis: str = Field(
        description="Primary diagnosis or assessment summarizing the encounter.",
    )
    primary_diagnosis_source: Optional[str] = Field(
        default=None,
        description="Section name where primary diagnosis was documented.",
    )
    secondary_diagnoses: List[str] = Field(
        default_factory=list,
        description="Secondary or contributing diagnoses explicitly discussed.",
    )
    clinical_reasoning: List[str] = Field(
        default_factory=list,
        description="Reasoning points explaining the clinical assessment (must be from documentation).",
    )
    medication_relationship: Optional[MedicationRelationship] = Field(
        default=None,
        description="Medication involvement in the presentation (null if not applicable).",
    )
    cause_determination: Optional[CauseDetermination] = Field(
        default=None,
        description="Precipitating cause when identified (null if not determined).",
    )
    fall_risk_assessment: Optional[FallRiskAssessment] = Field(
        default=None,
        description="Fall risk evaluation (null if falls not discussed).",
    )


class AssessmentExtractionResponse(BaseModel):
    clinical_assessment: AssessmentData
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


__all__ = [
    "MedicationRelationshipConfidence",
    "MedicationRelationship",
    "CauseDeterminationConfidence",
    "CauseDetermination",
    "FallRiskLevel",
    "FallRiskAssessment",
    "AssessmentData",
    "AssessmentExtractionResponse",
]

