"""Shared Pydantic models and enums for clinical summary extraction."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class MedicalConditionStatus(str, Enum):
    active = "active"
    resolved = "resolved"
    historical = "historical"


class MedicalCondition(BaseModel):
    condition_name: str = Field(
        description="Name of the medical condition (use standard clinical terminology)."
    )
    icd10_code: Optional[str] = Field(
        default=None,
        description="ICD-10 code ONLY if explicitly documented in the note."
    )
    icd10_source: Optional[str] = Field(
        default=None,
        description="Section name where ICD-10 code was documented."
    )
    severity: Optional[str] = Field(
        default=None,
        description="Severity, stage, grade, or class (e.g., 'Stage 3', 'NYHA Class II')."
    )
    status: MedicalConditionStatus = Field(
        description="Status of the condition: active, resolved, or historical."
    )
    status_rationale: str = Field(
        description="Justification for the assigned status based on documentation (required)."
    )
    location: Optional[str] = Field(
        default=None,
        description="Anatomical location when specified (e.g., 'Sacral region', 'Left knee')."
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional clinical context (baseline values, recent changes, management notes)."
    )
    documented_in_section: str = Field(
        description="Section name where this condition was found (required)."
    )


class LabStatus(str, Enum):
    critical = "critical"
    abnormal_high = "abnormal_high"
    abnormal_low = "abnormal_low"
    normal = "normal"


class LabCategory(str, Enum):
    chemistry = "chemistry"
    hematology = "hematology"
    coagulation = "coagulation"
    arterial_blood_gas = "arterial_blood_gas"
    urinalysis = "urinalysis"
    metabolic = "metabolic"
    cardiac = "cardiac"
    hepatic = "hepatic"
    renal = "renal"
    electrolytes = "electrolytes"
    endocrine = "endocrine"
    toxicology = "toxicology"


class LabChange(BaseModel):
    absolute: float
    percent: float
    direction: str


class LabTest(BaseModel):
    id: str = Field(
        description="Unique identifier (e.g., lab_001, lab_002)."
    )
    test_name: str = Field(
        description="Name of the laboratory test (normalized, e.g., 'Creatinine', 'BUN')."
    )
    test_category: Optional[LabCategory] = Field(
        default=None,
        description="Category of the test (chemistry, hematology, etc.)."
    )
    value: Union[str, float] = Field(
        description="Test result value (numeric or string)."
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of measurement (e.g., 'mg/dL', 'mmol/L')."
    )
    status: LabStatus = Field(
        description="Status: critical, abnormal_high, abnormal_low, or normal."
    )
    reference_range: Optional[str] = Field(
        default=None,
        description="Reference range as documented (e.g., '0.6-1.2')."
    )
    reference_range_min: Optional[float] = Field(
        default=None,
        description="Minimum reference value (numeric)."
    )
    reference_range_max: Optional[float] = Field(
        default=None,
        description="Maximum reference value (numeric)."
    )
    baseline_value: Optional[Union[str, float]] = Field(
        default=None,
        description="Patient's baseline value if documented."
    )
    clinical_significance: Optional[str] = Field(
        default=None,
        description="Clinical interpretation of the result."
    )
    documented_in_section: Optional[str] = Field(
        default=None,
        description="Section where this lab result was documented."
    )


class VitalSign(BaseModel):
    type: str
    value: str
    unit: Optional[str] = None
    interpretation: Optional[str] = None


class MedicationRelationshipConfidence(str, Enum):
    definite = "definite"
    probable = "probable"
    possible = "possible"


class MedicationRelationship(BaseModel):
    implicated_medications: List[str]
    mechanism: Optional[str] = None
    confidence: MedicationRelationshipConfidence


class InterventionType(str, Enum):
    medication = "medication"
    procedure = "procedure"
    monitoring = "monitoring"
    supportive_care = "supportive_care"
    therapeutic_intervention = "therapeutic_intervention"
    diagnostic_test = "diagnostic_test"


class InterventionCategory(str, Enum):
    cardiovascular = "cardiovascular"
    respiratory = "respiratory"
    renal = "renal"
    metabolic = "metabolic"
    infectious_disease = "infectious_disease"
    pain_management = "pain_management"
    nutritional = "nutritional"
    psychiatric = "psychiatric"
    other = "other"


class MedicationAction(str, Enum):
    started = "started"
    discontinued = "discontinued"
    dose_adjusted = "dose_adjusted"
    continued = "continued"
    switched = "switched"


class MedicationRoute(str, Enum):
    iv = "IV"
    oral = "oral"
    subcutaneous = "subcutaneous"
    intramuscular = "intramuscular"
    topical = "topical"
    inhalation = "inhalation"


class MedicationTreatment(BaseModel):
    medication_name: str = Field(
        description="Name of medication (generic preferred)."
    )
    route: MedicationRoute = Field(
        description="Route of administration."
    )
    dose: Optional[str] = Field(
        default=None,
        description="Dose with units (e.g., '1000mg', '10 units')."
    )
    frequency: Optional[str] = Field(
        default=None,
        description="Frequency (e.g., 'BID', 'Q6H', 'Daily')."
    )
    action: MedicationAction = Field(
        description="Action taken: started, discontinued, dose_adjusted, continued, switched."
    )
    reason_for_action: Optional[str] = Field(
        default=None,
        description="Clinical indication or reason for the action."
    )
    related_to_admission_reason: bool = Field(
        default=False,
        description="True if medication action directly related to admission diagnosis."
    )


class ProcedureDetails(BaseModel):
    procedure_name: str
    procedure_code: Optional[str] = None
    performed_by: Optional[str] = None
    approach: Optional[str] = None
    findings: Optional[str] = None
    specimens_collected: Optional[List[str]] = None


class Treatment(BaseModel):
    id: str = Field(
        description="Unique identifier (e.g., tx_001, tx_002)."
    )
    treatment_type: InterventionType = Field(
        description="Type of intervention."
    )
    category: InterventionCategory = Field(
        default=InterventionCategory.other,
        description="Clinical category of treatment."
    )
    description: str = Field(
        description="Brief description of the treatment or intervention."
    )
    clinical_indication: Optional[str] = Field(
        default=None,
        description="Medical reason or indication for the treatment."
    )
    started_at: Optional[str] = Field(
        default=None,
        description="When treatment started (date/time or relative timing like 'Hospital Day 1')."
    )
    ended_at: Optional[str] = Field(
        default=None,
        description="When treatment ended."
    )
    duration: Optional[str] = Field(
        default=None,
        description="Duration of treatment (e.g., '3 days', 'Ongoing')."
    )
    timing_qualifier: Optional[str] = Field(
        default=None,
        description="Timing context (e.g., 'During ED stay', 'Inpatient')."
    )
    location: Optional[str] = Field(
        default=None,
        description="Where treatment was administered (e.g., 'ED', 'ICU')."
    )
    outcome: Optional[str] = Field(
        default=None,
        description="Result or response to treatment."
    )
    complications: Optional[List[str]] = Field(
        default=None,
        description="Any documented complications from the treatment."
    )
    documented_in_section: Optional[str] = Field(
        default=None,
        description="Section where this treatment was documented."
    )
    medication_details: Optional[MedicationTreatment] = Field(
        default=None,
        description="Details for medication-type treatments."
    )
    procedure_details: Optional[ProcedureDetails] = Field(
        default=None,
        description="Details for procedure-type treatments."
    )


class CourseEvent(BaseModel):
    day: int
    event: str
    outcome: Optional[str] = None


class AppointmentUrgency(str, Enum):
    urgent = "urgent"
    routine = "routine"
    as_needed = "as_needed"


class Appointment(BaseModel):
    specialty: str
    urgency: AppointmentUrgency
    timeframe: Optional[str] = None


class LabSummary(BaseModel):
    total_tests: int = 0
    critical_count: int = 0
    abnormal_count: int = 0
    normal_count: int = 0


__all__ = [
    "MedicalCondition",
    "MedicalConditionStatus",
    "LabStatus",
    "LabCategory",
    "LabChange",
    "LabTest",
    "VitalSign",
    "MedicationRelationship",
    "MedicationRelationshipConfidence",
    "InterventionType",
    "InterventionCategory",
    "MedicationAction",
    "MedicationRoute",
    "MedicationTreatment",
    "ProcedureDetails",
    "Treatment",
    "CourseEvent",
    "Appointment",
    "AppointmentUrgency",
    "LabSummary",
]

