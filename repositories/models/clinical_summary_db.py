"""SQLAlchemy model for clinical_summaries table."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from database.base import Base


class ClinicalSummary(Base):
    """
    SQLAlchemy model for clinical_summaries table.
    
    Stores each section of the clinical summary in separate JSONB columns
    for better querying and indexing capabilities.
    """
    
    __tablename__ = "clinical_summaries"
    
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
    patient_presentation = Column(
        JSONB,
        nullable=True,
        comment="Patient presentation data (symptoms, chief complaint, vital signs)"
    )
    
    relevant_history = Column(
        JSONB,
        nullable=True,
        comment="Relevant medical history, allergies, medications"
    )
    
    clinical_findings = Column(
        JSONB,
        nullable=True,
        comment="Clinical findings from physical exam and observations"
    )
    
    clinical_assessment = Column(
        JSONB,
        nullable=True,
        comment="Clinical assessment, diagnoses, and reasoning"
    )
    
    hospital_course = Column(
        JSONB,
        nullable=True,
        comment="Hospital course and progression during stay"
    )
    
    follow_up_plan = Column(
        JSONB,
        nullable=True,
        comment="Follow-up plan and discharge instructions"
    )
    
    treatments_procedures = Column(
        JSONB,
        nullable=True,
        comment="Treatments, procedures, and interventions"
    )
    
    lab_results = Column(
        JSONB,
        nullable=True,
        comment="Lab test results"
    )
    
    # Database metadata
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment="Timestamp when the record was created"
    )
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return (
            f"<ClinicalSummary("
            f"id={self.id}, "
            f"patient_id={self.patient_id}, "
            f"hospitalization_id={self.hospitalization_id}"
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
            "patient_presentation": self.patient_presentation,
            "relevant_history": self.relevant_history,
            "clinical_findings": self.clinical_findings,
            "clinical_assessment": self.clinical_assessment,
            "hospital_course": self.hospital_course,
            "follow_up_plan": self.follow_up_plan,
            "treatments_procedures": self.treatments_procedures,
            "lab_results": self.lab_results,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

