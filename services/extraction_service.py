"""Main extraction service that orchestrates handlers."""

from typing import Dict, Any, Optional, List
import logging

from database.session import DatabaseSession
from handler.clinical_and_hospital_summary_extraction_handler import (
    ClinicalAndHospitalSummaryExtractionHandler,
)

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Main service that orchestrates extraction handlers.
    
    This service coordinates handlers to process clinical text
    and extract structured data. Designed for easy extensibility -
    new handlers can be added by registering them in __init__ or
    using the register_handler() method.
    
    Handler Registry Pattern:
    - Each handler is responsible for a specific extraction domain
    - Handlers can run independently or in coordination
    - Easy to add new handlers without modifying existing code
    """
    
    def __init__(self, db_session: DatabaseSession):
        """
        Initialize extraction service with handlers.
        
        Args:
            db_session: DatabaseSession instance for database operations
        """
        self.db_session = db_session
        
        # Handler registry - add new handlers here
        self.handlers: List[Any] = [
            ClinicalAndHospitalSummaryExtractionHandler(db_session),
        ]
        
        logger.info(
            f"Extraction service initialized with {len(self.handlers)} handler(s)"
        )
    
    def register_handler(self, handler: Any) -> None:
        """
        Register a new handler dynamically.
        
        This allows adding handlers after initialization,
        useful for plugin architectures or dynamic configuration.
        
        Args:
            handler: Handler instance to register
                    (must implement process(patient_id, raw_text, metadata))
        
        Example:
            service = ExtractionService(db_session)
            service.register_handler(RadiologyReportHandler(db_session))
        """
        self.handlers.append(handler)
        logger.info(f"Registered new handler: {handler.__class__.__name__}")
    
    async def process(
        self,
        patient_id: str,
        raw_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process extraction for clinical text using all registered handlers.
        
        This method runs all registered handlers and aggregates their results.
        Currently runs handlers sequentially, but can be modified to run
        handlers in parallel if they're independent.
        
        Args:
            patient_id: Patient identifier
            raw_text: Raw clinical text to extract from
            metadata: Optional metadata dictionary
            
        Returns:
            Dictionary containing aggregated results from all handlers.
            Structure depends on handlers, but typically:
            {
                'handler_name': {
                    'result_key': 'value',
                    ...
                },
                ...
            }
            
        Raises:
            Exception: If any handler fails
        """
        logger.info(
            f"Starting extraction for patient {patient_id} "
            f"with {len(self.handlers)} handler(s)"
        )
        
        all_results = {}
        
        try:
            # Process each handler
            # Note: Currently sequential, but can be made parallel with asyncio.gather()
            # if handlers are independent
            for handler in self.handlers:
                handler_name = handler.__class__.__name__
                logger.info(f"Processing handler: {handler_name}")
                
                handler_result = await handler.process(
                    patient_id=patient_id,
                    raw_text=raw_text,
                    metadata=metadata
                )
                
                # Add handler results to aggregate
                all_results.update(handler_result)
                
                logger.info(f"Handler {handler_name} completed successfully")
            
            logger.info(f"All handlers completed for patient {patient_id}")
            return all_results
            
        except Exception as e:
            logger.error(
                f"Extraction pipeline failed for patient {patient_id}: {e}",
                exc_info=True
            )
            raise
    
    def list_handlers(self) -> List[str]:
        """
        List all registered handlers.
        
        Returns:
            List of handler class names
        """
        return [handler.__class__.__name__ for handler in self.handlers]
