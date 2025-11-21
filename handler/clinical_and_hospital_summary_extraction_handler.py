"""Unified handler for clinical and hospital summary extraction."""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from database.session import DatabaseSession

# Clinical extractors
from extractors.clinical_summary_entity.presentation.tool import PresentationPydanticAITool
from extractors.clinical_summary_entity.history.tool import HistoryPydanticAITool
from extractors.clinical_summary_entity.findings.tool import FindingsPydanticAITool
from extractors.clinical_summary_entity.assessment.tool import AssessmentPydanticAITool
from extractors.clinical_summary_entity.course.tool import CoursePydanticAITool
from extractors.clinical_summary_entity.follow_up.tool import FollowUpPydanticAITool
from extractors.clinical_summary_entity.treatments.tool import TreatmentsPydanticAITool
from extractors.clinical_summary_entity.labs.tool import LabsPydanticAITool
from extractors.clinical_summary_entity.shared_models import LabStatus, LabSummary

# Clinical summary models
from extractors.clinical_summary_entity.aggregator import (
    ClinicalSummary,
    ClinicalSummaryMetadata,
    ClinicalSummaryResult,
)

# Hospital extractors
from extractors.hospital_admission_summary_card.facility_timing.tool import FacilityTimingPydanticAITool
from extractors.hospital_admission_summary_card.diagnosis.tool import DiagnosisPydanticAITool
from extractors.hospital_admission_summary_card.medication_risk.tool import MedicationRiskPydanticAITool
from extractors.hospital_admission_summary_card.model import HospitalAdmissionSummaryCard

# Repositories
from repositories.clinical_summary_repository import ClinicalSummaryRepository
from repositories.hospital_summary_repository import HospitalSummaryRepository
from repositories.models.clinical_summary_db import ClinicalSummary as ClinicalSummaryDB
from repositories.models.hospital_summary_db import HospitalSummary as HospitalSummaryDB

# Pydantic AI settings
from pydantic_ai_settings import pydantic_ai_settings

logger = logging.getLogger(__name__)


class ClinicalAndHospitalSummaryExtractionHandler:
    """
    Unified handler for clinical and hospital summary extraction.
    
    This handler:
    1. Generates a unique hospitalization_id (GUID) for data consistency
    2. Collects all 11 individual extractors (8 clinical + 3 hospital)
    3. Runs ALL extractors in parallel using asyncio.gather()
    4. Assembles results into clinical and hospital summaries
    5. Saves both results to their respective databases in parallel
    
    All extractions share the same hospitalization_id for data consistency.
    """
    
    def __init__(self, db_session: DatabaseSession):
        """
        Initialize handler with all individual extractors.
        
        Args:
            db_session: DatabaseSession instance for database operations
        """
        self.db_session = db_session
        
        # Clinical extractors (8 tools)
        self.presentation_tool = PresentationPydanticAITool()
        self.history_tool = HistoryPydanticAITool()
        self.findings_tool = FindingsPydanticAITool()
        self.assessment_tool = AssessmentPydanticAITool()
        self.course_tool = CoursePydanticAITool()
        self.follow_up_tool = FollowUpPydanticAITool()
        self.treatments_tool = TreatmentsPydanticAITool()
        self.labs_tool = LabsPydanticAITool()
        
        # Hospital extractors (3 tools)
        self.facility_timing_tool = FacilityTimingPydanticAITool()
        self.diagnosis_tool = DiagnosisPydanticAITool()
        self.medication_risk_tool = MedicationRiskPydanticAITool()
        
        logger.info("ClinicalAndHospitalSummaryExtractionHandler initialized with 11 extractors")
    
    async def process(
        self,
        patient_id: str,
        raw_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process all extractions for a patient document.
        
        This method:
        1. Generates a unique hospitalization_id (GUID)
        2. Runs ALL 11 extractors in parallel
        3. Assembles results into clinical and hospital summaries
        4. Saves both results to database with the same hospitalization_id
        
        Args:
            patient_id: Patient identifier
            raw_text: Raw clinical text
            metadata: Optional metadata
            
        Returns:
            Dictionary with extraction results:
            {
                'hospitalization_id': 'uuid-string',
                'clinical_summary': {
                    'id': 'uuid',
                    'patient_id': 'P-027',
                    'hospitalization_id': 'uuid',
                    'success': True
                },
                'hospital_summary': {
                    'id': 'uuid',
                    'patient_id': 'P-027',
                    'hospitalization_id': 'uuid',
                    'length_of_stay_days': 5,
                    'success': True
                }
            }
            
        Raises:
            Exception: If extraction or save fails
        """
        # Generate unique hospitalization ID
        hospitalization_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting extraction for patient {patient_id} "
            f"with hospitalization_id {hospitalization_id}"
        )
        
        try:
            # Step 1: Run ALL 11 extractors in parallel
            logger.info("Running all 11 extractors in parallel")
            
            # Create all extraction tasks
            tasks = [
                # Clinical extractors (8)
                self.presentation_tool.run(raw_text),
                self.history_tool.run(raw_text),
                self.findings_tool.run(raw_text),
                self.assessment_tool.run(raw_text),
                self.course_tool.run(raw_text),
                self.follow_up_tool.run(raw_text),
                self.treatments_tool.run(raw_text),
                self.labs_tool.run(raw_text),
                # Hospital extractors (3)
                self.facility_timing_tool.run(raw_text),
                self.diagnosis_tool.run(raw_text),
                self.medication_risk_tool.run(raw_text),
            ]
            
            # Execute all in parallel
            (
                presentation_resp,
                history_resp,
                findings_resp,
                assessment_resp,
                course_resp,
                follow_up_resp,
                treatments_resp,
                labs_resp,
                facility_timing_resp,
                diagnosis_resp,
                medication_risk_resp,
            ) = await asyncio.gather(*tasks)
            
            logger.info(
                f"All 11 extractors completed for patient {patient_id}, "
                f"hospitalization {hospitalization_id}"
            )
            
            # Step 2: Assemble clinical summary result
            logger.info("Assembling clinical summary")
            clinical_summary = self._assemble_clinical_summary(
                patient_id=patient_id,
                hospitalization_id=hospitalization_id,
                raw_text=raw_text,
                presentation_resp=presentation_resp,
                history_resp=history_resp,
                findings_resp=findings_resp,
                assessment_resp=assessment_resp,
                course_resp=course_resp,
                follow_up_resp=follow_up_resp,
                treatments_resp=treatments_resp,
                labs_resp=labs_resp,
            )
            
            # Step 3: Assemble hospital summary result
            logger.info("Assembling hospital summary")
            hospital_summary = self._assemble_hospital_summary(
                hospitalization_id=hospitalization_id,
                facility_timing_resp=facility_timing_resp,
                diagnosis_resp=diagnosis_resp,
                medication_risk_resp=medication_risk_resp,
            )
            
            # Step 4: Save both to database in parallel
            logger.info("Saving results to database")
            
            save_tasks = [
                self._save_clinical_summary(patient_id, clinical_summary),
                self._save_hospital_summary(patient_id, hospital_summary),
            ]
            
            clinical_db_record, hospital_db_record = await asyncio.gather(*save_tasks)
            
            logger.info(
                f"Successfully saved all records for hospitalization {hospitalization_id}: "
                f"clinical_id={clinical_db_record.id}, hospital_id={hospital_db_record.id}"
            )
            
            # Return structured results
            return {
                'hospitalization_id': hospitalization_id,
                'clinical_summary': {
                    'id': str(clinical_db_record.id),
                    'patient_id': clinical_db_record.patient_id,
                    'hospitalization_id': clinical_db_record.hospitalization_id,
                    'success': True
                },
                'hospital_summary': {
                    'id': str(hospital_db_record.id),
                    'patient_id': hospital_db_record.patient_id,
                    'hospitalization_id': hospital_db_record.hospitalization_id,
                    'length_of_stay_days': hospital_db_record.length_of_stay_days,
                    'success': True
                }
            }
            
        except Exception as e:
            logger.error(
                f"Failed to process extraction for patient {patient_id}, "
                f"hospitalization {hospitalization_id}: {e}",
                exc_info=True
            )
            raise
    
    def _assemble_clinical_summary(
        self,
        patient_id: str,
        hospitalization_id: str,
        raw_text: str,
        presentation_resp,
        history_resp,
        findings_resp,
        assessment_resp,
        course_resp,
        follow_up_resp,
        treatments_resp,
        labs_resp,
    ) -> ClinicalSummaryResult:
        """
        Assemble clinical summary from extractor results.
        
        This mimics what the ClinicalSummaryExtractor.extract() method does,
        but with pre-extracted results from individual tools.
        
        Args:
            patient_id: Patient identifier
            hospitalization_id: Generated hospitalization ID
            raw_text: Original raw text
            *_resp: Individual extractor responses
            
        Returns:
            ClinicalSummaryResult ready for database storage
        """
        # Add IDs to all responses
        presentation_resp = presentation_resp.model_copy(
            update={"patient_id": patient_id, "hospitalization_id": hospitalization_id}
        )
        history_resp = history_resp.model_copy(
            update={"patient_id": patient_id, "hospitalization_id": hospitalization_id}
        )
        findings_resp = findings_resp.model_copy(
            update={"patient_id": patient_id, "hospitalization_id": hospitalization_id}
        )
        assessment_resp = assessment_resp.model_copy(
            update={"patient_id": patient_id, "hospitalization_id": hospitalization_id}
        )
        course_resp = course_resp.model_copy(
            update={"patient_id": patient_id, "hospitalization_id": hospitalization_id}
        )
        follow_up_resp = follow_up_resp.model_copy(
            update={"patient_id": patient_id, "hospitalization_id": hospitalization_id}
        )
        treatments_resp = treatments_resp.model_copy(
            update={"patient_id": patient_id, "hospitalization_id": hospitalization_id}
        )
        labs_resp = labs_resp.model_copy(
            update={"patient_id": patient_id, "hospitalization_id": hospitalization_id}
        )
        
        # Build clinical summary
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
        
        # Build metadata
        metadata = ClinicalSummaryMetadata(
            hospitalization_id=hospitalization_id,
            patient_id=patient_id,
            raw_summary_text=raw_text,
            parsed_at=datetime.now(timezone.utc),
            parsing_model_version=pydantic_ai_settings.model_name,
        )
        
        return ClinicalSummaryResult(summary=summary, metadata=metadata)
    
    def _assemble_hospital_summary(
        self,
        hospitalization_id: str,
        facility_timing_resp,
        diagnosis_resp,
        medication_risk_resp,
    ) -> HospitalAdmissionSummaryCard:
        """
        Assemble hospital summary from extractor results.
        
        This mimics what HospitalAdmissionSummaryCardExtractor.extract() does,
        but with pre-extracted results from individual tools.
        
        Args:
            hospitalization_id: Generated hospitalization ID
            facility_timing_resp: Facility timing extraction response
            diagnosis_resp: Diagnosis extraction response
            medication_risk_resp: Medication risk extraction response
            
        Returns:
            HospitalAdmissionSummaryCard ready for database storage
        """
        # Ensure assessed_at timestamp is set
        if not medication_risk_resp.medication_risk_assessment.assessed_at:
            medication_risk_resp.medication_risk_assessment.assessed_at = (
                datetime.now(timezone.utc).isoformat()
            )
        
        # Build summary card with generated hospitalization_id
        summary_card = HospitalAdmissionSummaryCard(
            facility=facility_timing_resp.facility,
            timing=facility_timing_resp.timing,
            diagnosis=diagnosis_resp.diagnosis,
            medication_risk_assessment=medication_risk_resp.medication_risk_assessment,
            hospitalization_id=hospitalization_id,
        )
        
        return summary_card
    
    @staticmethod
    def _ensure_lab_summary(labs_resp) -> LabSummary:
        """
        Ensure lab summary has counts calculated.
        
        If the LLM didn't provide counts, calculate them from lab results.
        
        Args:
            labs_resp: Lab extraction response with lab_results and lab_summary
            
        Returns:
            LabSummary with proper counts
        """
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
    
    async def _save_clinical_summary(
        self,
        patient_id: str,
        extraction_result: ClinicalSummaryResult
    ) -> ClinicalSummaryDB:
        """
        Save clinical summary to database.
        
        Args:
            patient_id: Patient identifier
            extraction_result: ClinicalSummaryResult from assembly
            
        Returns:
            Saved ClinicalSummary database record
        """
        async with self.db_session.get_session() as session:
            repository = ClinicalSummaryRepository(session)
            
            db_record = await repository.create({
                'patient_id': patient_id,
                'summary': extraction_result
            })
        
        logger.info(f"Clinical summary saved: record_id={db_record.id}")
        return db_record
    
    async def _save_hospital_summary(
        self,
        patient_id: str,
        extraction_result: HospitalAdmissionSummaryCard
    ) -> HospitalSummaryDB:
        """
        Save hospital summary to database.
        
        Args:
            patient_id: Patient identifier
            extraction_result: HospitalAdmissionSummaryCard from assembly
            
        Returns:
            Saved HospitalSummary database record
        """
        async with self.db_session.get_session() as session:
            repository = HospitalSummaryRepository(session)
            
            db_record = await repository.create({
                'patient_id': patient_id,
                'summary_card': extraction_result
            })
        
        logger.info(f"Hospital summary saved: record_id={db_record.id}")
        return db_record

