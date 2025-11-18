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


class PresentationType(str, Enum):
    """Type of clinical presentation."""
    A = "A"  # Medication-Related Presentation
    B = "B"  # Medication Present But Unrelated
    C = "C"  # Medication Management Needed But Not Causative


class Metadata(BaseModel):
    """Metadata about the note and analysis."""
    note_type: str = Field(
        description="Type of clinical note (emergency_visit, inpatient_admission, observation, outpatient_visit)."
    )
    sections_reviewed: List[str] = Field(
        default_factory=list,
        description="List of note sections reviewed during analysis.",
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="List of missing key information.",
    )
    model_uncertainty_notes: List[str] = Field(
        default_factory=list,
        description="Any uncertainties or conflicting data.",
    )


class ClinicalContext(BaseModel):
    """Clinical context of the presentation."""
    presentation_type: PresentationType = Field(
        description="Classification of presentation type (A, B, or C)."
    )
    presentation_type_rationale: str = Field(
        description="Brief explanation of why Type A/B/C was assigned."
    )
    primary_reason_for_presentation: str = Field(
        description="1-2 sentence summary of primary reason for presentation."
    )
    is_medication_related: bool = Field(
        description="Whether this presentation is medication-related."
    )
    medication_relationship_explanation: str = Field(
        description="Explanation of why this is/isn't medication-related."
    )
    patient_clinical_status: str = Field(
        description="Patient clinical status (critical, unstable, stable_at_baseline, improved)."
    )
    organ_dysfunction: List[str] = Field(
        default_factory=list,
        description="List of organ dysfunctions (renal, hepatic, cardiac, neurologic).",
    )


class RiskScoring(BaseModel):
    """Evidence-based risk scoring breakdown."""
    positive_evidence_points: int = Field(
        ge=0,
        description="Sum of positive evidence points."
    )
    negative_evidence_points: int = Field(
        ge=0,
        description="Sum of negative evidence points."
    )
    net_score: int = Field(
        description="Net score (positive minus negative)."
    )
    score_breakdown: str = Field(
        description="Detailed breakdown of scoring."
    )


class LikelihoodPercentage(BaseModel):
    """Likelihood percentage with supporting evidence."""
    percentage: int = Field(
        ge=0,
        le=100,
        description="Likelihood of medication-related problem (0-100%)."
    )
    evidence: str = Field(
        description="Brief summary of key evidence supporting this likelihood."
    )
    calculation_method: str = Field(
        default="evidence_scoring_system",
        description="Method used to calculate likelihood."
    )


class RiskFactor(BaseModel):
    """Individual risk factor with detailed evidence."""
    factor: str = Field(
        description="Clear, specific description of risk factor."
    )
    evidence: str = Field(
        description="Direct quotes with quantitative data, locations, temporal relationships, evidence strength rating."
    )
    severity: RiskSeverity = Field(
        description="Severity level of this risk factor."
    )
    severity_rationale: str = Field(
        description="Explanation of why this severity was assigned."
    )
    implicated_medications: List[str] = Field(
        default_factory=list,
        description="Medications involved in this risk factor with doses.",
    )
    mechanism: str = Field(
        description="How this medication causes this risk."
    )
    temporal_relationship: str = Field(
        description="Timeline of events."
    )


class AlternativeExplanation(BaseModel):
    """Alternative non-medication explanation for the presentation."""
    explanation: str = Field(
        description="Non-medication cause of presentation."
    )
    likelihood: str = Field(
        description="Likelihood of alternative explanation (high, medium, low)."
    )
    supporting_evidence: str = Field(
        description="Evidence supporting this alternative explanation."
    )
    impact_on_medication_assessment: str = Field(
        description="How this affects medication causality assessment."
    )


class RiskAssessment(BaseModel):
    """Complete medication risk assessment."""
    metadata: Metadata = Field(
        description="Metadata about the note and analysis."
    )
    clinical_context: ClinicalContext = Field(
        description="Clinical context of the presentation."
    )
    risk_scoring: RiskScoring = Field(
        description="Evidence-based risk scoring breakdown."
    )
    likelihood_percentage: LikelihoodPercentage = Field(
        description="Likelihood percentage with supporting evidence."
    )
    risk_level: RiskLevel = Field(
        description="Derived risk level: high (70-100%), medium (30-69%), low (0-29%)."
    )
    risk_factors: List[RiskFactor] = Field(
        default_factory=list,
        description="List of identified risk factors with detailed evidence."
    )
    alternative_explanations: List[AlternativeExplanation] = Field(
        default_factory=list,
        description="Alternative non-medication explanations for presentation."
    )
    negative_findings: List[str] = Field(
        default_factory=list,
        description="What was looked for but not found."
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="AI confidence in the assessment (0.0-1.0)."
    )
    confidence_rationale: str = Field(
        description="Explanation of why this confidence level was assigned."
    )
    assessment_method: AssessmentMethod = Field(
        default=AssessmentMethod.ai_analysis,
        description="Method used for assessment."
    )
    assessed_at: str = Field(
        description="ISO 8601 timestamp when assessment was performed."
    )


class MedicationRiskExtractionResponse(BaseModel):
    medication_risk_assessment: RiskAssessment

    def to_standardizer(self) -> dict:
        return self.model_dump()


__all__ = [
    "RiskSeverity",
    "RiskLevel",
    "AssessmentMethod",
    "PresentationType",
    "Metadata",
    "ClinicalContext",
    "RiskScoring",
    "LikelihoodPercentage",
    "RiskFactor",
    "AlternativeExplanation",
    "RiskAssessment",
    "MedicationRiskExtractionResponse",
]

