"""Hospital summary extractor - wrapper for HospitalAdmissionSummaryCardExtractor."""

from typing import Any, Dict, Optional
import logging

from extraction_service.core.base_extractor import BaseExtractor
from extraction_service.core.exceptions import LLMExtractionError, ValidationError
from extraction_service.core.registry import registry
from extraction_service.extractors.hospital_admission_summary_card.aggregator import (
    HospitalAdmissionSummaryCardExtractor,
)

logger = logging.getLogger(__name__)


class HospitalSummaryExtractor(BaseExtractor):
    """
    Extractor for hospital_summaries table.
    
    Wraps the existing HospitalAdmissionSummaryCardExtractor which runs
    three LLM tools in parallel:
    - FacilityTimingPydanticAITool (for facility and timing data)
    - DiagnosisPydanticAITool (for diagnosis data)
    - MedicationRiskPydanticAITool (for medication risk assessment)
    """
    
    def __init__(self):
        """Initialize hospital summary extractor."""
        super().__init__(name="hospital_summary", version="1.0.0")
        
        # Initialize the aggregator that runs all LLM tools
        self._aggregator = HospitalAdmissionSummaryCardExtractor()
        
        logger.info("Hospital summary extractor initialized with aggregator")
    
    @property
    def table_name(self) -> str:
        """Get database table name."""
        return "hospital_summaries"
    
    async def extract(
        self,
        patient_id: str,
        raw_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract hospital summary data from clinical text.
        
        Args:
            patient_id: Patient identifier
            raw_text: Raw clinical text
            metadata: Optional metadata (not used currently)
            
        Returns:
            Dictionary with keys matching HospitalSummary table:
            - patient_id (str)
            - summary_card (HospitalAdmissionSummaryCard - Pydantic model)
            
        Raises:
            LLMExtractionError: If extraction fails
            ValidationError: If validation fails
        """
        # Validate input
        self.validate_input(patient_id, raw_text)
        
        logger.info(f"Extracting hospital summary for patient {patient_id}")
        
        try:
            # Run the aggregator (runs 3 LLM tools, some in parallel)
            summary_card = await self._aggregator.extract(raw_text)
            
            # Validate extracted data
            self._validate_extraction(summary_card)
            
            # Return dictionary matching database table structure
            # Note: Pydantic model (summary_card) is included directly
            # It will be automatically serialized by PydanticJSONB
            result = {
                "patient_id": patient_id,
                "summary_card": summary_card,  # HospitalAdmissionSummaryCard Pydantic model
            }
            
            logger.info(
                f"Extraction successful: hospitalization_id={summary_card.hospitalization_id}, "
                f"length_of_stay={summary_card.length_of_stay_days} days"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Hospital summary extraction failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LLMExtractionError(
                message=error_msg,
                extractor_name=self.name
            ) from e
    
    def _validate_extraction(self, summary_card) -> None:
        """
        Validate extracted data quality.
        
        Args:
            summary_card: HospitalAdmissionSummaryCard instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Check hospitalization_id (optional, can be None)
        if not summary_card.hospitalization_id:
            logger.warning("hospitalization_id is None - will be set by database")
        
        # Check length of stay is reasonable
        if summary_card.length_of_stay_days < 0:
            raise ValidationError(
                "Length of stay cannot be negative",
                field="length_of_stay_days",
                value=summary_card.length_of_stay_days
            )
        
        if summary_card.length_of_stay_days > 365:
            logger.warning(
                f"Unusually long stay: {summary_card.length_of_stay_days} days"
            )
        
        # Check facility name
        if not summary_card.facility.facility_name:
            raise ValidationError(
                "Facility name is required",
                field="facility.facility_name"
            )
        
        # Check primary diagnosis
        if not summary_card.diagnosis.primary_diagnosis:
            raise ValidationError(
                "Primary diagnosis is required",
                field="diagnosis.primary_diagnosis"
            )
        
        logger.debug("Extraction validation passed")


# Auto-register this extractor when the module is imported
registry.register(HospitalSummaryExtractor())

