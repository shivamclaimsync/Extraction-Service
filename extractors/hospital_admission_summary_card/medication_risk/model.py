"""Models for medication risk assessment extraction."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RiskSeverity(str, Enum):
    critical = "critical"
    major = "major"
    moderate = "moderate"
    minor = "minor"


class RiskLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class AssessmentMethod(str, Enum):
    ai_analysis = "ai_analysis"
    pharmacist_determination = "pharmacist_determination"
    combined = "combined"


class RiskFactor(BaseModel):
    """Individual risk factor with evidence."""
    factor: str = Field(
        description="Clear, specific description of risk factor."
    )
    evidence: str = Field(
        description="Supporting evidence with direct quotes and quantitative data."
    )
    severity: RiskSeverity = Field(
        description="Severity level: critical, major, moderate, or minor."
    )
    implicated_medications: Optional[List[str]] = Field(
        default=None,
        description="List of medication names involved in this risk factor."
    )


class MedicationRiskAssessment(BaseModel):
    """Medication risk assessment for hospitalization."""
    likelihood_percentage: int = Field(
        ge=0,
        le=100,
        description="Likelihood of medication-related hospitalization (0-100%)."
    )
    risk_level: RiskLevel = Field(
        description="Derived risk level: high (70-100%), medium (30-69%), low (0-29%)."
    )
    risk_factors: List[RiskFactor] = Field(
        default_factory=list,
        description="List of identified risk factors."
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="AI confidence in the assessment (0.0-1.0)."
    )
    assessment_method: AssessmentMethod = Field(
        default=AssessmentMethod.ai_analysis,
        description="Method used for assessment."
    )
    assessed_at: str = Field(
        description="ISO 8601 timestamp when assessment was performed."
    )


class MedicationRiskExtractionResponse(BaseModel):
    medication_risk_assessment: MedicationRiskAssessment

    def to_standardizer(self) -> dict:
        return self.model_dump()


__all__ = [
    "RiskSeverity",
    "RiskLevel",
    "AssessmentMethod",
    "RiskFactor",
    "MedicationRiskAssessment",
    "MedicationRiskExtractionResponse",
]
