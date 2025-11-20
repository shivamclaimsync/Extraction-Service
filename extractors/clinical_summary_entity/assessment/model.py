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
    mechanism: str = Field(
        description="How medications contributed to the presentation.",
    )
    evidence: str = Field(
        description="Section name and direct quote supporting the mechanism.",
    )
    confidence: MedicationRelationshipConfidence = Field(
        description="Level of confidence in medication relationship.",
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
    contributing_factors: List[str] = Field(
        default_factory=list,
        description="Documented risk factors contributing to fall risk.",
    )


class SecondaryDiagnosis(BaseModel):
    diagnosis: str = Field(
        description="Secondary diagnosis text (verbatim from note).",
    )
    source: str = Field(
        description="Section name where this diagnosis was found.",
    )
    relationship: str = Field(
        description="Relationship to primary diagnosis: pre-existing condition, contributing factor, complication of, acute exacerbation, concurrent acute condition.",
    )


class AssessmentData(BaseModel):
    primary_diagnosis: str = Field(
        description="Primary diagnosis or assessment summarizing the encounter.",
    )
    primary_diagnosis_source: Optional[str] = Field(
        default=None,
        description="Section name where primary diagnosis was documented.",
    )
    secondary_diagnoses: List[SecondaryDiagnosis] = Field(
        default_factory=list,
        description="Secondary or contributing diagnoses with source and relationship.",
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
    "SecondaryDiagnosis",
    "AssessmentData",
    "AssessmentExtractionResponse",
]
