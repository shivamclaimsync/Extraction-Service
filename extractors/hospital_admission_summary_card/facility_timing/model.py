"""Models for facility and timing data extraction."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FacilityType(str, Enum):
    acute_care = "acute_care"
    psychiatric = "psychiatric"
    rehabilitation = "rehabilitation"
    ltac = "ltac"


class Address(BaseModel):
    street: Optional[str] = Field(
        default=None,
        description="Street address of the facility.",
    )
    city: str = Field(description="City where the facility is located.")
    state: str = Field(description="State where the facility is located.")
    zip: Optional[str] = Field(
        default=None,
        description="ZIP code of the facility.",
    )


class FacilityData(BaseModel):
    facility_name: str = Field(description="Name of the healthcare facility.")
    facility_id: Optional[str] = Field(
        default=None,
        description="External facility identifier if available in the document.",
    )
    facility_type: FacilityType = Field(
        default=FacilityType.acute_care,
        description="Type of healthcare facility.",
    )
    address: Optional[Address] = Field(
        default=None,
        description="Physical address of the facility.",
    )


class AdmissionSource(str, Enum):
    emergency_dept = "emergency_dept"
    direct_admission = "direct_admission"
    transfer = "transfer"
    scheduled = "scheduled"


class DischargeDisposition(str, Enum):
    home = "home"
    snf = "snf"
    home_health = "home_health"
    rehab = "rehab"
    transfer = "transfer"
    expired = "expired"


class TimingData(BaseModel):
    admission_date: str = Field(
        description="Admission date in ISO 8601 format (e.g., '2025-10-15T14:30:00Z').",
    )
    admission_time: Optional[str] = Field(
        default=None,
        description="Admission time in HH:MM format if separately documented.",
    )
    discharge_date: str = Field(
        description="Discharge date in ISO 8601 format.",
    )
    discharge_time: Optional[str] = Field(
        default=None,
        description="Discharge time in HH:MM format if separately documented.",
    )
    admission_source: Optional[AdmissionSource] = Field(
        default=None,
        description="How the patient arrived at the facility.",
    )
    discharge_disposition: Optional[DischargeDisposition] = Field(
        default=None,
        description="Where the patient went after discharge.",
    )

    @property
    def length_of_stay_days(self) -> int:
        """Calculate length of stay from admission to discharge dates."""
        try:
            admission = datetime.fromisoformat(self.admission_date.replace('Z', '+00:00'))
            discharge = datetime.fromisoformat(self.discharge_date.replace('Z', '+00:00'))
            delta = discharge - admission
            return max(0, delta.days)
        except (ValueError, AttributeError):
            return 0


class FacilityTimingExtractionResponse(BaseModel):
    facility: FacilityData
    timing: TimingData
    patient_id: Optional[str] = Field(
        default=None,
        description="Patient identifier extracted from the clinical note (e.g., MRN, Patient ID field)."
    )
    hospitalization_id: Optional[str] = Field(
        default=None,
        description="Hospitalization/encounter identifier extracted from the clinical note (e.g., DOC_ID, Encounter ID, Account Number)."
    )

    def to_standardizer(self) -> dict:
        data = self.model_dump()
        # Add computed length of stay
        data["timing"]["length_of_stay_days"] = self.timing.length_of_stay_days
        return data


__all__ = [
    "Address",
    "FacilityType",
    "FacilityData",
    "AdmissionSource",
    "DischargeDisposition",
    "TimingData",
    "FacilityTimingExtractionResponse",
]

