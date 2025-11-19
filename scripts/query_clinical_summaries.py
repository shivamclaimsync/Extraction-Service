#!/usr/bin/env python3
"""
Query and display clinical summaries from the database.

Usage:
    python -m extraction_service.scripts.query_clinical_summaries
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from extraction_service.config import settings
from extraction_service.database.session import init_db
from extraction_service.services.extraction_service import ExtractionService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def query_summaries():
    """Query all clinical summaries."""
    try:
        logger.info("="*80)
        logger.info("CLINICAL SUMMARIES IN DATABASE")
        logger.info("="*80)
        
        db_session = init_db(
            database_url=settings.effective_database_url,
            echo=False
        )
        
        service = ExtractionService(db_session)
        
        # Get all records (using a high limit)
        records = await service.get_record(
            table_name="clinical_summaries",
            patient_id="any",  # This will be ignored, we'll get all
            limit=100
        )
        
        # If records is not a list, make it one
        if not isinstance(records, list):
            records = [records] if records else []
        
        logger.info(f"\nFound {len(records)} record(s)")
        
        for i, record in enumerate(records, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Record #{i}")
            logger.info(f"{'='*60}")
            logger.info(f"ID: {record.id}")
            logger.info(f"Patient ID: {record.patient_id}")
            logger.info(f"Hospitalization ID: {record.hospitalization_id}")
            logger.info(f"Created: {record.created_at}")
            
            if record.summary:
                summary = record.summary.summary
                metadata = record.summary.metadata
                
                logger.info(f"\n--- Summary Data ---")
                if summary.patient_presentation:
                    symptoms = summary.patient_presentation.symptoms or []
                    logger.info(f"Symptoms: {', '.join(symptoms[:5])}")
                
                if summary.clinical_assessment:
                    logger.info(f"Primary Diagnosis: {summary.clinical_assessment.primary_diagnosis or 'N/A'}")
                    logger.info(f"Assessment Summary: {summary.clinical_assessment.assessment_summary or 'N/A'}")
                
                if summary.treatments_procedures:
                    logger.info(f"Treatments: {len(summary.treatments_procedures)} recorded")
                
                if summary.lab_results:
                    logger.info(f"Lab Results: {len(summary.lab_results)} tests")
                
                logger.info(f"\n--- Metadata ---")
                logger.info(f"Parsed at: {metadata.parsed_at}")
                logger.info(f"Model version: {metadata.parsing_model_version}")
            else:
                logger.warning("No summary data found")
        
        await db_session.close()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"TOTAL: {len(records)} clinical summaries in database")
        logger.info(f"{'='*80}\n")
        
        return len(records)
        
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        return 0


async def main():
    """Main execution."""
    try:
        count = await query_summaries()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

