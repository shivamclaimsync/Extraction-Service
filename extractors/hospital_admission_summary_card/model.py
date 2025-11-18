"""Root model for hospital admission summary card."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .diagnosis.model import DiagnosisData
from .facility_timing.model import FacilityData, TimingData
from .medication_risk.model import RiskAssessment


class HospitalAdmissionSummaryCard(BaseModel):
    """Complete hospital admission summary card combining all extracted data."""

    facility: FacilityData = Field(
        description="Facility where care was provided."
    )
    timing: TimingData = Field(
        description="Admission and discharge timing information."
    )
    diagnosis: DiagnosisData = Field(
        description="Primary and secondary diagnoses."
    )
    medication_risk_assessment: RiskAssessment = Field(
        description="Medication-related risk assessment."
    )
    hospitalization_id: Optional[str] = Field(
        default=None,
        description="Hospitalization/encounter identifier extracted from the clinical note."
    )

    @property
    def length_of_stay_days(self) -> int:
        """Calculate length of stay from timing data."""
        return self.timing.length_of_stay_days

    def to_standardizer(self) -> dict:
        """Convert to dictionary format for downstream processing."""
        data = self.model_dump()
        # Include computed length of stay
        data["length_of_stay_days"] = self.length_of_stay_days
        return data


__all__ = ["HospitalAdmissionSummaryCard"]

