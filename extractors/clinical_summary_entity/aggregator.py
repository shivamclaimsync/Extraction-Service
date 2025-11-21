"""Clinical summary models for aggregation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from .presentation.model import PresentationData
from .history.model import HistoryData
from .findings.model import FindingsData
from .assessment.model import AssessmentData
from .course.model import CourseData
from .follow_up.model import FollowUpData
from .shared_models import LabSummary, LabTest, Treatment


class ClinicalSummaryMetadata(BaseModel):
    """Metadata for clinical summary extraction."""
    
    hospitalization_id: Optional[str] = None
    patient_id: Optional[str] = None
    raw_summary_text: Optional[str] = None
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parsing_model_version: Optional[str] = None
    confidence_score: Optional[float] = None


class ClinicalSummary(BaseModel):
    """Aggregated clinical summary with all sections."""
    
    patient_presentation: PresentationData
    relevant_history: HistoryData
    clinical_findings: FindingsData
    clinical_assessment: AssessmentData
    hospital_course: CourseData
    follow_up_plan: FollowUpData
    treatments_procedures: list[Treatment] = Field(default_factory=list)
    lab_results: list[LabTest] = Field(default_factory=list)
    lab_summary: LabSummary = Field(default_factory=LabSummary)

    def to_standardizer(self) -> dict:
        """Convert to dictionary representation."""
        return self.model_dump()


class ClinicalSummaryResult(BaseModel):
    """Result containing clinical summary and metadata."""
    
    summary: ClinicalSummary
    metadata: ClinicalSummaryMetadata

    def to_standardizer(self) -> dict:
        """Convert to dictionary representation."""
        data = self.summary.to_standardizer()
        data["metadata"] = self.metadata.model_dump()
        return data


__all__ = [
    "ClinicalSummary",
    "ClinicalSummaryMetadata",
    "ClinicalSummaryResult",
]

