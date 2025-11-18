"""SQLAlchemy model for hospital_summaries table."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from extraction_service.database.base import Base
from extraction_service.database.types import PydanticJSONB

# Import the complete Pydantic model from extractors
from extraction_service.extractors.hospital_admission_summary_card.model import (
    HospitalAdmissionSummaryCard,
)


class HospitalSummary(Base):
    """
    SQLAlchemy model for hospital_summaries table.
    
    Uses PydanticJSONB to store the entire HospitalAdmissionSummaryCard Pydantic model
    in a single JSONB column. This eliminates structural duplication - the same model
    used for LLM extraction is stored directly in the database.
    
    Database-specific fields (id, patient_id, created_at) are kept separate for
    efficient querying and indexing.
    """
    
    __tablename__ = "hospital_summaries"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    
    # Patient identifier (indexed for efficient queries)
    patient_id = Column(
        Text,
        nullable=False,
        index=True,
        comment="Patient identifier"
    )
    
    # Single JSONB column storing the complete summary card
    summary_card = Column(
        PydanticJSONB(HospitalAdmissionSummaryCard),
        nullable=False,
        comment="Complete hospital admission summary card with facility, timing, "
                "diagnosis, and medication risk assessment"
    )
    
    # Database metadata
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment="Timestamp when the record was created"
    )
    
    # Convenience properties for backward compatibility and easier access
    @property
    def hospitalization_id(self) -> str | None:
        """Get hospitalization_id from summary_card."""
        return self.summary_card.hospitalization_id if self.summary_card else None
    
    @property
    def facility(self):
        """Get facility data from summary_card."""
        return self.summary_card.facility if self.summary_card else None
    
    @property
    def timing(self):
        """Get timing data from summary_card."""
        return self.summary_card.timing if self.summary_card else None
    
    @property
    def diagnosis(self):
        """Get diagnosis data from summary_card."""
        return self.summary_card.diagnosis if self.summary_card else None
    
    @property
    def medication_risk_assessment(self):
        """Get medication risk assessment from summary_card."""
        return self.summary_card.medication_risk_assessment if self.summary_card else None
    
    @property
    def length_of_stay_days(self) -> int:
        """Get length of stay from summary_card."""
        return self.summary_card.length_of_stay_days if self.summary_card else 0
    
    def __repr__(self) -> str:
        """String representation of the model."""
        facility_name = (
            self.summary_card.facility.facility_name
            if self.summary_card and self.summary_card.facility
            else None
        )
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
        
        Note: The summary_card is automatically converted back to a Pydantic
        instance when queried, so you can access properties like
        self.summary_card.facility.facility_name
        """
        return {
            "id": str(self.id),
            "patient_id": self.patient_id,
            "hospitalization_id": self.hospitalization_id,
            "summary_card": self.summary_card.model_dump() if self.summary_card else None,
            "length_of_stay_days": self.length_of_stay_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

