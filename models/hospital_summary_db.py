"""SQLAlchemy model for hospital_summaries table."""

import uuid

from sqlalchemy import Column, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from extraction_service.database.base import Base


class HospitalSummary(Base):
    """
    SQLAlchemy model for hospital_summaries table.
    
    Stores each section of the hospital admission summary in separate JSONB columns
    for better querying and indexing capabilities.
    """
    
    __tablename__ = "hospital_summaries"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # Identifiers
    hospitalization_id = Column(
        Text,
        nullable=True,
        index=True,
        comment="Hospitalization/encounter identifier"
    )
    
    patient_id = Column(
        Text,
        nullable=False,
        index=True,
        comment="Patient identifier"
    )
    
    # Separate JSONB columns for each section
    facility = Column(
        JSONB,
        nullable=False,
        comment="Facility information (JSONB)"
    )
    
    timing = Column(
        JSONB,
        nullable=False,
        comment="Admission and discharge timing (JSONB)"
    )
    
    diagnosis = Column(
        JSONB,
        nullable=False,
        comment="Primary and secondary diagnoses (JSONB)"
    )
    
    medication_risk_assessment = Column(
        JSONB,
        nullable=False,
        comment="Medication risk assessment (JSONB)"
    )
    
    # Computed/metadata fields
    length_of_stay_days = Column(
        Integer,
        nullable=False,
        comment="Length of stay in days (computed from timing)"
    )
    
    def __repr__(self) -> str:
        """String representation of the model."""
        facility_name = None
        if self.facility and isinstance(self.facility, dict):
            facility_name = self.facility.get("facility_name")
        return (
            f"<HospitalSummary("
            f"id={self.id}, "
            f"patient_id={self.patient_id}, "
            f"hospitalization_id={self.hospitalization_id}, "
            f"facility={facility_name}"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary representation.
        """
        return {
            "id": str(self.id),
            "patient_id": self.patient_id,
            "hospitalization_id": self.hospitalization_id,
            "facility": self.facility,
            "timing": self.timing,
            "diagnosis": self.diagnosis,
            "medication_risk_assessment": self.medication_risk_assessment,
            "length_of_stay_days": self.length_of_stay_days,
        }

