"""Entry point for the extraction service."""

import asyncio
import logging
from typing import Dict, Any

from core.logging import setup_logging
from config import settings
from database.session import init_db
from services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


async def main(
    patient_id: str,
    raw_text: str,
) -> Dict[str, Any]:
    """
    Main execution function for extraction service.
    
    Args:
        patient_id: Patient identifier
        raw_text: Raw clinical text to process
        
    Returns:
        Dictionary with extraction results including:
        - hospitalization_id: Generated GUID
        - clinical_summary: Clinical summary extraction results
        - hospital_summary: Hospital summary extraction results
    """
    logger.info("Starting extraction service")
    
    # Initialize database
    db_session = init_db(
        database_url=settings.effective_database_url,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )
    
    try:
        # Create extraction service
        extraction_service = ExtractionService(db_session=db_session)
        
        # Process extraction
        results = await extraction_service.process(
            patient_id=patient_id,
            raw_text=raw_text,
        )
        
        logger.info("Extraction completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        raise
    finally:
        await db_session.close()


if __name__ == "__main__":
    # Setup logging first
    setup_logging()
    
    # Example usage - replace with your actual data
    # In production, you might read from files, API, or message queue
    
    sample_text = """
    Patient ID: P-027
    
    Chief Complaint: Chest pain
    
    History of Present Illness:
    Patient presents with acute onset chest pain...
    
    [Add full clinical text here]
    """
    
    # Run extraction
    results = asyncio.run(
        main(
            patient_id="P-027",
            raw_text=sample_text,
        )
    )
    
   

