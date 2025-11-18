"""Aggregator that combines clinical summary section tools."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

try:
    from new.pydantic_ai_settings import pydantic_ai_settings
except ImportError:
    from extraction_service.pydantic_ai_settings import pydantic_ai_settings

from .assessment.model import AssessmentData
from .assessment.tool import AssessmentPydanticAITool
from .course.model import CourseData
from .course.tool import CoursePydanticAITool
from .findings.model import FindingsData
from .findings.tool import FindingsPydanticAITool
from .follow_up.model import FollowUpData
from .follow_up.tool import FollowUpPydanticAITool
from .history.model import HistoryData
from .history.tool import HistoryPydanticAITool
from .labs.model import LabExtractionResponse
from .labs.tool import LabsPydanticAITool
from .presentation.model import PresentationData, PresentationExtractionResponse
from .presentation.tool import PresentationPydanticAITool
from .shared_models import LabStatus, LabSummary, LabTest, Treatment
from .treatments.model import TreatmentsExtractionResponse
from .treatments.tool import TreatmentsPydanticAITool

logger = logging.getLogger(__name__)


class ClinicalSummaryMetadata(BaseModel):
    hospitalization_id: Optional[str] = None
    patient_id: Optional[str] = None
    raw_summary_text: Optional[str] = None
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parsing_model_version: Optional[str] = None
    confidence_score: Optional[float] = None


class ClinicalSummary(BaseModel):
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
        return self.model_dump()


class ClinicalSummaryResult(BaseModel):
    summary: ClinicalSummary
    metadata: ClinicalSummaryMetadata

    def to_standardizer(self) -> dict:
        data = self.summary.to_standardizer()
        data["metadata"] = self.metadata.model_dump()
        return data


@dataclass
class ClinicalSummaryExtractor:
    presentation_tool: PresentationPydanticAITool = field(default_factory=PresentationPydanticAITool)
    history_tool: HistoryPydanticAITool = field(default_factory=HistoryPydanticAITool)
    findings_tool: FindingsPydanticAITool = field(default_factory=FindingsPydanticAITool)
    assessment_tool: AssessmentPydanticAITool = field(default_factory=AssessmentPydanticAITool)
    course_tool: CoursePydanticAITool = field(default_factory=CoursePydanticAITool)
    follow_up_tool: FollowUpPydanticAITool = field(default_factory=FollowUpPydanticAITool)
    treatments_tool: TreatmentsPydanticAITool = field(default_factory=TreatmentsPydanticAITool)
    labs_tool: LabsPydanticAITool = field(default_factory=LabsPydanticAITool)

    async def extract(
        self,
        clinical_text: str,
        metadata: Optional[ClinicalSummaryMetadata] = None,
    ) -> ClinicalSummaryResult:
        metadata = metadata or ClinicalSummaryMetadata()
        metadata_payload = metadata.model_dump()
        if metadata_payload.get("raw_summary_text") is None:
            metadata_payload["raw_summary_text"] = clinical_text
        if metadata_payload.get("parsing_model_version") is None:
            metadata_payload["parsing_model_version"] = pydantic_ai_settings.model_name
        
        # Extract patient_id and hospitalization_id from clinical text if not in metadata
        patient_id = metadata_payload.get("patient_id")
        hospitalization_id = metadata_payload.get("hospitalization_id")
        
        if not patient_id:
            # Try to extract Patient ID from text
            patient_id_match = re.search(r'Patient ID:\s*(\S+)', clinical_text)
            if patient_id_match:
                patient_id = patient_id_match.group(1).strip()
            else:
                # Try MRN pattern
                mrn_match = re.search(r'MRN[:\s]+(\S+)', clinical_text, re.IGNORECASE)
                if mrn_match:
                    patient_id = mrn_match.group(1).strip()
        
        if not hospitalization_id:
            # Try to extract DOC_ID from text
            doc_id_match = re.search(r'DOC_ID:([a-f0-9-]+)', clinical_text, re.IGNORECASE)
            if doc_id_match:
                hospitalization_id = doc_id_match.group(1).strip()
            else:
                # Try Encounter ID pattern
                enc_match = re.search(r'Encounter ID[:\s]+(\S+)', clinical_text, re.IGNORECASE)
                if enc_match:
                    hospitalization_id = enc_match.group(1).strip()
        
        # Update metadata with extracted IDs
        metadata_payload["patient_id"] = patient_id
        metadata_payload["hospitalization_id"] = hospitalization_id
        metadata = ClinicalSummaryMetadata(**metadata_payload)
        
        logger.info(
            "Extracted metadata - Patient ID: %s, Hospitalization ID: %s",
            patient_id,
            hospitalization_id
        )

        tasks = [
            self.presentation_tool.run(clinical_text),
            self.history_tool.run(clinical_text),
            self.findings_tool.run(clinical_text),
            self.assessment_tool.run(clinical_text),
            self.course_tool.run(clinical_text),
            self.follow_up_tool.run(clinical_text),
            self.treatments_tool.run(clinical_text),
            self.labs_tool.run(clinical_text),
        ]

        (
            presentation_resp,
            history_resp,
            findings_resp,
            assessment_resp,
            course_resp,
            follow_up_resp,
            treatments_resp,
            labs_resp,
        ) = await asyncio.gather(*tasks)
        
        # Add IDs to all responses using model_copy (Pydantic v2)
        presentation_resp = presentation_resp.model_copy(update={"patient_id": patient_id, "hospitalization_id": hospitalization_id})
        history_resp = history_resp.model_copy(update={"patient_id": patient_id, "hospitalization_id": hospitalization_id})
        findings_resp = findings_resp.model_copy(update={"patient_id": patient_id, "hospitalization_id": hospitalization_id})
        assessment_resp = assessment_resp.model_copy(update={"patient_id": patient_id, "hospitalization_id": hospitalization_id})
        course_resp = course_resp.model_copy(update={"patient_id": patient_id, "hospitalization_id": hospitalization_id})
        follow_up_resp = follow_up_resp.model_copy(update={"patient_id": patient_id, "hospitalization_id": hospitalization_id})
        treatments_resp = treatments_resp.model_copy(update={"patient_id": patient_id, "hospitalization_id": hospitalization_id})
        labs_resp = labs_resp.model_copy(update={"patient_id": patient_id, "hospitalization_id": hospitalization_id})

        summary = ClinicalSummary(
            patient_presentation=presentation_resp.patient_presentation,
            relevant_history=history_resp.relevant_history,
            clinical_findings=findings_resp.clinical_findings,
            clinical_assessment=assessment_resp.clinical_assessment,
            hospital_course=course_resp.hospital_course,
            follow_up_plan=follow_up_resp.follow_up_plan,
            treatments_procedures=treatments_resp.treatments_procedures,
            lab_results=labs_resp.lab_results,
            lab_summary=self._ensure_lab_summary(labs_resp),
        )

        return ClinicalSummaryResult(summary=summary, metadata=metadata)

    @staticmethod
    def _ensure_lab_summary(labs_resp: LabExtractionResponse) -> LabSummary:
        summary = labs_resp.lab_summary
        if summary.total_tests and summary.total_tests > 0:
            return summary

        total = len(labs_resp.lab_results)
        critical = sum(1 for lab in labs_resp.lab_results if lab.status == LabStatus.critical)
        abnormal = sum(
            1
            for lab in labs_resp.lab_results
            if lab.status in {LabStatus.abnormal_high, LabStatus.abnormal_low}
        )
        normal = total - critical - abnormal

        return LabSummary(
            total_tests=total,
            critical_count=critical,
            abnormal_count=abnormal,
            normal_count=normal,
        )


__all__ = [
    "ClinicalSummaryExtractor",
    "ClinicalSummary",
    "ClinicalSummaryMetadata",
    "ClinicalSummaryResult",
]

