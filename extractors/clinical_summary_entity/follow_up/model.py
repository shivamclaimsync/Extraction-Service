"""Models for follow-up plan extraction."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AppointmentUrgency(str, Enum):
    urgent = "urgent"
    routine = "routine"
    as_needed = "as_needed"


class FollowUpAppointment(BaseModel):
    specialty: str = Field(
        description="Specialty or type of follow-up (e.g., 'Primary Care', 'Cardiology', 'Wound Care')."
    )
    urgency: AppointmentUrgency = Field(
        description="Urgency level: urgent (<1 week), routine (1-4 weeks), as_needed (PRN or no specific timeframe)."
    )
    timeframe: Optional[str] = Field(
        default=None,
        description="Specific timeframe (e.g., 'Within 2-4 days', '1-2 weeks', '3 months')."
    )
    provider: Optional[str] = Field(
        default=None,
        description="Specific provider name when documented."
    )
    location: Optional[str] = Field(
        default=None,
        description="Clinic or facility location when specified."
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional context or instructions for the appointment."
    )


class CareCoordination(BaseModel):
    services: List[str] = Field(
        default_factory=list,
        description="External services arranged (e.g., 'Home Health', 'Skilled Nursing Facility', 'Outpatient PT')."
    )
    responsible_team: Optional[str] = Field(
        default=None,
        description="Team or individual responsible for coordination."
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Specific coordination instructions or handoff details."
    )


class FollowUpData(BaseModel):
    appointments: List[FollowUpAppointment] = Field(
        default_factory=list,
        description="Scheduled or recommended follow-up appointments."
    )
    discharge_instructions: List[str] = Field(
        default_factory=list,
        description="Patient-facing instructions for care at home (activity, medications, wound care, return precautions)."
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Clinical recommendations for monitoring or future management (distinct from instructions)."
    )
    patient_education: List[str] = Field(
        default_factory=list,
        description="Educational topics discussed or materials provided."
    )
    care_transitions: List[str] = Field(
        default_factory=list,
        description="Transitions in care setting (e.g., 'Discharge to home', 'Transfer to SNF')."
    )
    care_coordination: Optional[CareCoordination] = Field(
        default=None,
        description="External care coordination details (null if none)."
    )


class FollowUpExtractionResponse(BaseModel):
    follow_up_plan: FollowUpData
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
    "AppointmentUrgency",
    "FollowUpAppointment",
    "CareCoordination",
    "FollowUpData",
    "FollowUpExtractionResponse",
]

