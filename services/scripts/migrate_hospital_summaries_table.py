#!/usr/bin/env python3
"""
Migrate hospital_summaries table from old schema to new schema.

Old schema: Separate JSONB columns (facility, timing, diagnosis, medication_risk_assessment, length_of_stay_days)
New schema: Single JSONB column (summary_card) with complete summary

Usage:
    python -m extraction_service.scripts.migrate_hospital_summaries_table
"""

import asyncio
import sys
from pathlib import Path
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from extraction_service.config import settings
from extraction_service.database.session import init_db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_table():
    """Migrate the hospital_summaries table."""
    try:
        logger.info("="*80)
        logger.info("HOSPITAL SUMMARIES TABLE MIGRATION")
        logger.info("="*80)
        
        db_session = init_db(
            database_url=settings.effective_database_url,
            echo=False,
            pool_size=1,
            max_overflow=0
        )
        
        async with db_session.get_session() as session:
            # Step 1: Check current row count
            result = await session.execute(text("SELECT COUNT(*) FROM hospital_summaries"))
            current_count = result.scalar()
            logger.info(f"Current records in table: {current_count}")
            
            if current_count > 0:
                logger.warning(f"⚠ Table contains {current_count} record(s)")
                logger.info("  These records will be preserved during migration")
            
            # Step 2: Check if we need to migrate (check if 'summary_card' column exists)
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'hospital_summaries' AND column_name = 'summary_card'
            """))
            summary_card_column_exists = result.scalar() is not None
            
            if summary_card_column_exists:
                logger.info("✓ Table already has 'summary_card' column - migration not needed")
                # Check if it's the right type
                result = await session.execute(text("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'hospital_summaries' AND column_name = 'summary_card'
                """))
                data_type = result.scalar()
                logger.info(f"  Column type: {data_type}")
                await db_session.close()
                return True
            
            # Step 3: Backup existing data if any
            backup_data = []
            if current_count > 0:
                logger.info("\nStep 1: Backing up existing data...")
                result = await session.execute(text("""
                    SELECT id, hospitalization_id, patient_id,
                           facility, timing, diagnosis, medication_risk_assessment,
                           length_of_stay_days, created_at
                    FROM hospital_summaries
                """))
                backup_data = result.fetchall()
                logger.info(f"✓ Backed up {len(backup_data)} records")
            
            # Step 4: Drop old columns and add new summary_card column
            logger.info("\nStep 2: Modifying table structure...")
            
            # Add new summary_card column first
            await session.execute(text("""
                ALTER TABLE hospital_summaries 
                ADD COLUMN IF NOT EXISTS summary_card jsonb
            """))
            logger.info("✓ Added 'summary_card' column")
            
            # Step 5: Migrate data if there was any
            if backup_data:
                logger.info("\nStep 3: Migrating existing data to new schema...")
                for row in backup_data:
                    (id, hosp_id, pat_id, facility, timing, diagnosis, 
                     med_risk, los_days, created) = row
                    
                    # Construct the new summary_card structure
                    new_summary_card = {
                        "facility": facility or {},
                        "timing": timing or {},
                        "diagnosis": diagnosis or {},
                        "medication_risk_assessment": med_risk or {},
                        "hospitalization_id": hosp_id
                    }
                    
                    # Update the record
                    await session.execute(
                        text("""
                            UPDATE hospital_summaries 
                            SET summary_card = :summary_card 
                            WHERE id = :id
                        """),
                        {"summary_card": json.dumps(new_summary_card), "id": id}
                    )
                
                await session.commit()
                logger.info(f"✓ Migrated {len(backup_data)} records")
            
            # Step 6: Drop old columns
            logger.info("\nStep 4: Removing old columns...")
            old_columns = [
                'hospitalization_id', 'facility', 'timing', 
                'diagnosis', 'medication_risk_assessment', 'length_of_stay_days'
            ]
            
            for col in old_columns:
                try:
                    await session.execute(text(f"""
                        ALTER TABLE hospital_summaries 
                        DROP COLUMN IF EXISTS {col}
                    """))
                    logger.info(f"✓ Dropped column: {col}")
                except Exception as e:
                    logger.warning(f"⚠ Could not drop column {col}: {e}")
            
            await session.commit()
            
            # Step 7: Make summary_card NOT NULL if there's no data
            if current_count == 0:
                await session.execute(text("""
                    ALTER TABLE hospital_summaries 
                    ALTER COLUMN summary_card SET NOT NULL
                """))
                logger.info("✓ Set summary_card column to NOT NULL")
            
            # Step 8: Add GIN index for efficient JSON queries
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_hospital_summaries_summary_card_gin 
                    ON public.hospital_summaries USING gin (summary_card)
            """))
            logger.info("✓ Added GIN index on summary_card")
            
            # Step 9: Verify final structure
            logger.info("\nStep 5: Verifying new structure...")
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'hospital_summaries'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            logger.info("New table structure:")
            for col in columns:
                logger.info(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
            
            await session.commit()
        
        await db_session.close()
        
        logger.info("\n" + "="*80)
        logger.info("✓ MIGRATION COMPLETE")
        logger.info("="*80)
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}", exc_info=True)
        return False


async def main():
    """Main execution."""
    try:
        success = await migrate_table()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

