#!/usr/bin/env python3
"""
Verify all records in both clinical_summaries and hospital_summaries tables.
"""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from database.session import init_db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def verify_all():
    """Verify all records."""
    try:
        db_session = init_db(database_url=settings.effective_database_url, echo=False)
        
        print("\n" + "="*80)
        print("DATABASE RECORDS VERIFICATION")
        print("="*80)
        
        async with db_session.get_session() as session:
            # Clinical summaries
            result = await session.execute(text("SELECT COUNT(*) FROM clinical_summaries"))
            clinical_count = result.scalar()
            
            print(f"\n📊 CLINICAL SUMMARIES: {clinical_count} records")
            
            if clinical_count > 0:
                result = await session.execute(text("""
                    SELECT 
                        id, 
                        patient_id, 
                        created_at,
                        summary->'metadata'->>'hospitalization_id' as hosp_id,
                        summary->'summary'->'clinical_assessment'->>'primary_diagnosis' as diagnosis
                    FROM clinical_summaries
                    ORDER BY created_at DESC
                    LIMIT 10
                """))
                records = result.fetchall()
                
                for i, rec in enumerate(records, 1):
                    print(f"\n  {i}. Patient: {rec[1]}")
                    print(f"     Record ID: {rec[0]}")
                    print(f"     Hospitalization: {rec[3] or 'N/A'}")
                    print(f"     Diagnosis: {rec[4] or 'N/A'}")
                    print(f"     Created: {rec[2]}")
            
            # Hospital summaries
            result = await session.execute(text("SELECT COUNT(*) FROM hospital_summaries"))
            hospital_count = result.scalar()
            
            print(f"\n🏥 HOSPITAL SUMMARIES: {hospital_count} records")
            
            if hospital_count > 0:
                result = await session.execute(text("""
                    SELECT 
                        id, 
                        patient_id, 
                        created_at,
                        summary_card->>'hospitalization_id' as hosp_id,
                        summary_card->'facility'->>'facility_name' as facility,
                        summary_card->'diagnosis'->>'primary_diagnosis' as diagnosis,
                        summary_card->'medication_risk_assessment'->>'risk_level' as risk
                    FROM hospital_summaries
                    ORDER BY created_at DESC
                    LIMIT 10
                """))
                records = result.fetchall()
                
                for i, rec in enumerate(records, 1):
                    print(f"\n  {i}. Patient: {rec[1]}")
                    print(f"     Record ID: {rec[0]}")
                    print(f"     Hospitalization: {rec[3] or 'N/A'}")
                    print(f"     Facility: {rec[4] or 'N/A'}")
                    print(f"     Diagnosis: {rec[5] or 'N/A'}")
                    print(f"     Risk Level: {rec[6] or 'N/A'}")
                    print(f"     Created: {rec[2]}")
        
        await db_session.close()
        
        print("\n" + "="*80)
        print(f"TOTAL RECORDS: {clinical_count + hospital_count}")
        print(f"  - Clinical Summaries: {clinical_count}")
        print(f"  - Hospital Summaries: {hospital_count}")
        print("="*80 + "\n")
        
        return clinical_count + hospital_count
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 0


async def main():
    count = await verify_all()
    sys.exit(0)


if __name__ == '__main__':
    asyncio.run(main())

