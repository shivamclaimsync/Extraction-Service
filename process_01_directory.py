#!/usr/bin/env python3
"""Process all files in the 01 directory through the extraction service."""

import asyncio
import logging
from pathlib import Path

from core.logging import setup_logging
from config import settings
from database.session import init_db
from services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


async def process_file(
    extraction_service: ExtractionService,
    file_path: Path,
    patient_id: str = "P-027"
) -> dict:
    """Process a single file through the extraction service."""
    logger.info(f"Processing file: {file_path.name}")
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    # Process extraction
    results = await extraction_service.process(
        patient_id=patient_id,
        raw_text=raw_text,
    )
    
    logger.info(
        f"✓ Completed {file_path.name}: "
        f"hospitalization_id={results['hospitalization_id']}"
    )
    
    return results


async def main():
    """Process all files in the 01 directory."""
    setup_logging()
    logger.info("Starting batch processing of 01 directory")
    
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
        
        # Get all .txt files from 01 directory
        directory = Path("01")
        files = sorted(directory.glob("*.txt"))
        
        if not files:
            logger.warning(f"No .txt files found in {directory}")
            return
        
        logger.info(f"Found {len(files)} file(s) to process")
        
        # Process each file
        results = []
        for file_path in files:
            try:
                result = await process_file(
                    extraction_service=extraction_service,
                    file_path=file_path,
                    patient_id="P-027"
                )
                results.append({
                    'file': file_path.name,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}", exc_info=True)
                results.append({
                    'file': file_path.name,
                    'error': str(e)
                })
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("PROCESSING SUMMARY")
        logger.info("="*60)
        for item in results:
            if 'error' in item:
                logger.error(f"✗ {item['file']}: {item['error']}")
            else:
                r = item['result']
                logger.info(
                    f"✓ {item['file']}: "
                    f"hospitalization_id={r['hospitalization_id']}, "
                    f"clinical_id={r['clinical_summary']['id']}, "
                    f"hospital_id={r['hospital_summary']['id']}"
                )
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}", exc_info=True)
        raise
    finally:
        await db_session.close()


if __name__ == "__main__":
    asyncio.run(main())

