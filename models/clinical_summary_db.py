"""SQLAlchemy model for clinical_summaries table."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from extraction_service.database.base import Base
from extraction_service.database.types import PydanticJSONB

# Import the complete Pydantic model from extractors
from extraction_service.extractors.clinical_summary_entity.aggregator import (
    ClinicalSummaryResult,
)


class ClinicalSummary(Base):
    """
    SQLAlchemy model for clinical_summaries table.
    
    Uses PydanticJSONB to store the entire ClinicalSummaryResult Pydantic model
    in a single JSONB column. This eliminates structural duplication - the same model
    used for LLM extraction is stored directly in the database.
    
    Database-specific fields (id, patient_id, created_at) are kept separate for
    efficient querying and indexing.
    """
    
    __tablename__ = "clinical_summaries"
    
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
    
    # Single JSONB column storing the complete summary result
    summary = Column(
        PydanticJSONB(ClinicalSummaryResult),
        nullable=False,
        comment="Complete clinical summary with presentation, history, findings, "
                "assessment, course, follow-up, treatments, and lab results"
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
        """Get hospitalization_id from summary metadata."""
        return self.summary.metadata.hospitalization_id if self.summary else None
    
    @property
    def patient_presentation(self):
        """Get patient presentation from summary."""
        return self.summary.summary.patient_presentation if self.summary else None
    
    @property
    def lab_results(self):
        """Get lab results from summary."""
        return self.summary.summary.lab_results if self.summary else []
    
    @property
    def lab_summary(self):
        """Get lab summary from summary."""
        return self.summary.summary.lab_summary if self.summary else None
    
    def __repr__(self) -> str:
        """String representation of the model."""
        hospitalization_id = (
            self.summary.metadata.hospitalization_id
            if self.summary and self.summary.metadata
            else None
        )
        return (
            f"<ClinicalSummary("
            f"id={self.id}, "
            f"patient_id={self.patient_id}, "
            f"hospitalization_id={hospitalization_id}"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary representation.
        
        Note: The summary is automatically converted back to a Pydantic
        instance when queried, so you can access properties like
        self.summary.summary.patient_presentation
        """
        return {
            "id": str(self.id),
            "patient_id": self.patient_id,
            "hospitalization_id": self.hospitalization_id,
            "summary": self.summary.model_dump() if self.summary else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

