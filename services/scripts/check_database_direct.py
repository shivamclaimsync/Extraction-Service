#!/usr/bin/env python3
"""
Check database records directly using SQL.
"""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from extraction_service.config import settings
from extraction_service.database.session import init_db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_records():
    """Check records directly."""
    try:
        db_session = init_db(database_url=settings.effective_database_url, echo=False)
        
        async with db_session.get_session() as session:
            # Get count
            result = await session.execute(text("SELECT COUNT(*) FROM clinical_summaries"))
            count = result.scalar()
            logger.info(f"Total records: {count}")
            
            # Get all records
            result = await session.execute(text("""
                SELECT id, patient_id, created_at,
                       summary->'metadata'->>'hospitalization_id' as hosp_id,
                       summary->'summary'->'patient_presentation'->>'symptoms' as symptoms
                FROM clinical_summaries
                ORDER BY created_at DESC
                LIMIT 10
            """))
            records = result.fetchall()
            
            logger.info(f"\nRecent records:")
            for i, rec in enumerate(records, 1):
                logger.info(f"\n{i}. ID: {rec[0]}")
                logger.info(f"   Patient: {rec[1]}")
                logger.info(f"   Created: {rec[2]}")
                logger.info(f"   Hosp ID: {rec[3]}")
                logger.info(f"   Symptoms: {rec[4][:100] if rec[4] else 'N/A'}...")
        
        await db_session.close()
        return count
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 0


async def main():
    count = await check_records()
    sys.exit(0)


if __name__ == '__main__':
    asyncio.run(main())

