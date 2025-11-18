"""Clinical summary extractor - wrapper for ClinicalSummaryExtractor."""

from typing import Any, Dict, Optional
import logging

from extraction_service.core.base_extractor import BaseExtractor
from extraction_service.core.exceptions import LLMExtractionError, ValidationError
from extraction_service.core.registry import registry
from extraction_service.extractors.clinical_summary_entity.aggregator import (
    ClinicalSummaryExtractor as ClinicalSummaryEntityExtractor,
    ClinicalSummaryResult,
)

logger = logging.getLogger(__name__)


class ClinicalSummaryExtractor(BaseExtractor):
    """
    Extractor for clinical_summaries table.
    
    Wraps the existing ClinicalSummaryEntityExtractor which runs
    eight LLM tools in parallel:
    - PresentationPydanticAITool (patient presentation)
    - HistoryPydanticAITool (relevant history)
    - FindingsPydanticAITool (clinical findings)
    - AssessmentPydanticAITool (clinical assessment)
    - CoursePydanticAITool (hospital course)
    - FollowUpPydanticAITool (follow-up plan)
    - TreatmentsPydanticAITool (treatments and procedures)
    - LabsPydanticAITool (lab results)
    """
    
    def __init__(self):
        """Initialize clinical summary extractor."""
        super().__init__(name="clinical_summary", version="1.0.0")
        
        # Initialize the aggregator that runs all LLM tools
        self._aggregator = ClinicalSummaryEntityExtractor()
        
        logger.info("Clinical summary extractor initialized with aggregator")
    
    @property
    def table_name(self) -> str:
        """Get database table name."""
        return "clinical_summaries"
    
    async def extract(
        self,
        patient_id: str,
        raw_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract clinical summary data from clinical text.
        
        Args:
            patient_id: Patient identifier
            raw_text: Raw clinical text
            metadata: Optional metadata dictionary
            
        Returns:
            Dictionary with keys matching ClinicalSummary table:
            - patient_id (str)
            - summary (ClinicalSummaryResult - Pydantic model)
            
        Raises:
            LLMExtractionError: If extraction fails
            ValidationError: If validation fails
        """
        # Validate input
        self.validate_input(patient_id, raw_text)
        
        logger.info(f"Extracting clinical summary for patient {patient_id}")
        
        try:
            # Prepare metadata if provided
            from extraction_service.extractors.clinical_summary_entity.aggregator import (
                ClinicalSummaryMetadata,
            )
            
            extractor_metadata = None
            if metadata:
                extractor_metadata = ClinicalSummaryMetadata(
                    patient_id=patient_id,
                    hospitalization_id=metadata.get("hospitalization_id"),
                    raw_summary_text=raw_text,
                    parsing_model_version=metadata.get("parsing_model_version"),
                    confidence_score=metadata.get("confidence_score"),
                )
            else:
                extractor_metadata = ClinicalSummaryMetadata(
                    patient_id=patient_id,
                    raw_summary_text=raw_text,
                )
            
            # Run the aggregator (runs 8 LLM tools in parallel)
            result: ClinicalSummaryResult = await self._aggregator.extract(
                clinical_text=raw_text,
                metadata=extractor_metadata
            )
            
            # Validate extracted data
            self._validate_extraction(result)
            
            # Return dictionary matching database table structure
            # Note: Pydantic model (result) is included directly
            # It will be automatically serialized by PydanticJSONB
            return {
                "patient_id": patient_id,
                "summary": result,  # ClinicalSummaryResult Pydantic model
            }
            
        except Exception as e:
            error_msg = f"Clinical summary extraction failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LLMExtractionError(
                message=error_msg,
                extractor_name=self.name
            ) from e
    
    def _validate_extraction(self, result: ClinicalSummaryResult) -> None:
        """
        Validate extracted data quality.
        
        Args:
            result: ClinicalSummaryResult instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Check patient_id
        if not result.metadata.patient_id:
            logger.warning("patient_id is None in metadata")
        
        # Check that we have at least some data
        if not result.summary.patient_presentation:
            raise ValidationError(
                "Patient presentation is required",
                field="summary.patient_presentation"
            )
        
        # Check lab summary is valid
        if result.summary.lab_summary.total_tests < 0:
            raise ValidationError(
                "Lab summary total_tests cannot be negative",
                field="summary.lab_summary.total_tests",
                value=result.summary.lab_summary.total_tests
            )
        
        logger.debug("Extraction validation passed")


# Auto-register this extractor when the module is imported
registry.register(ClinicalSummaryExtractor())

