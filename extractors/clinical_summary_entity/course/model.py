"""Models for hospital course extraction."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CourseEvent(BaseModel):
    event: str = Field(
        description="Description of a key clinical event during the encounter."
    )
    time: Optional[str] = Field(
        default=None,
        description="Timing of the event (date/time, hospital day, or relative timing like 'On arrival')."
    )
    details: Optional[str] = Field(
        default=None,
        description="Additional context or details about the event."
    )


class CourseData(BaseModel):
    timeline: List[CourseEvent] = Field(
        default_factory=list,
        description="Chronological sequence of key clinical events (patient status changes, outcomes, responses)."
    )
    narrative_summary: Optional[str] = Field(
        default=None,
        description="Brief narrative summary of the overall clinical course (2-4 sentences)."
    )
    disposition: Optional[str] = Field(
        default=None,
        description="Final disposition: discharged_home, discharged_home_with_services, admitted_observation, admitted_inpatient, transferred, left_AMA, deceased."
    )
    length_of_stay: Optional[str] = Field(
        default=None,
        description="Duration of encounter (e.g., '3 hours', '2 days', 'Same day discharge')."
    )
    patient_response: Optional[str] = Field(
        default=None,
        description="Overall patient response to treatment and clinical course."
    )
    admission_date: Optional[str] = Field(
        default=None,
        description="Admission date in YYYY-MM-DD format."
    )
    discharge_date: Optional[str] = Field(
        default=None,
        description="Discharge date in YYYY-MM-DD format."
    )
    follow_up_plans: List[str] = Field(
        default_factory=list,
        description="Documented follow-up instructions and plans."
    )


class CourseExtractionResponse(BaseModel):
    hospital_course: CourseData
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
    "CourseEvent",
    "CourseData",
    "CourseExtractionResponse",
]

