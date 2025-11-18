"""Models for clinical findings extraction."""

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, Field

from ..shared_models import LabTest


class VitalSignMeasurement(BaseModel):
    measurement: str = Field(
        description="Type of vital sign (e.g., 'Blood Pressure', 'Heart Rate', 'Temperature')."
    )
    value: Union[str, float] = Field(
        description="Measured value."
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of measurement (e.g., 'mmHg', 'bpm', '°C')."
    )
    status: Optional[str] = Field(
        default=None,
        description="Interpretation: normal, abnormal_high, abnormal_low."
    )
    clinical_significance: Optional[str] = Field(
        default=None,
        description="Clinical interpretation when abnormal."
    )


class PhysicalExamFinding(BaseModel):
    system: str = Field(
        description="Body system (e.g., 'HEENT', 'Cardiovascular', 'Respiratory')."
    )
    finding: str = Field(
        description="Description of the finding."
    )
    status: Optional[str] = Field(
        default=None,
        description="Status indicator: normal or abnormal."
    )


class ImagingStudy(BaseModel):
    study: str = Field(
        description="Name of imaging study (e.g., 'CT Head without contrast')."
    )
    date: Optional[str] = Field(
        default=None,
        description="Date of the study."
    )
    findings: List[str] = Field(
        default_factory=list,
        description="List of specific findings from the study."
    )
    impression: Optional[str] = Field(
        default=None,
        description="Radiologist's impression or summary."
    )


class AnthropometricMeasurement(BaseModel):
    value: Union[float, int] = Field(
        description="Measured value."
    )
    unit: str = Field(
        description="Unit of measurement."
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional context (e.g., 'Lost 70 pounds')."
    )


class AnthropometricData(BaseModel):
    height: Optional[AnthropometricMeasurement] = Field(
        default=None,
        description="Patient height."
    )
    weight: Optional[AnthropometricMeasurement] = Field(
        default=None,
        description="Patient weight."
    )
    bmi: Optional[AnthropometricMeasurement] = Field(
        default=None,
        description="Body Mass Index."
    )


class FindingsData(BaseModel):
    lab_results: List[LabTest] = Field(
        default_factory=list,
        description="List of significant laboratory results."
    )
    vital_signs: Optional[List[VitalSignMeasurement]] = Field(
        default=None,
        description="Documented vital signs."
    )
    physical_exam_findings: Optional[List[PhysicalExamFinding]] = Field(
        default=None,
        description="Physical examination findings."
    )
    imaging_findings: Optional[List[ImagingStudy]] = Field(
        default=None,
        description="Imaging studies and results."
    )
    anthropometrics: Optional[AnthropometricData] = Field(
        default=None,
        description="Height, weight, BMI measurements."
    )
    diagnostic_notes: Optional[dict] = Field(
        default=None,
        description="Additional diagnostic context (key-value pairs)."
    )


class FindingsExtractionResponse(BaseModel):
    clinical_findings: FindingsData
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


__all__ = ["FindingsData", "FindingsExtractionResponse"]

