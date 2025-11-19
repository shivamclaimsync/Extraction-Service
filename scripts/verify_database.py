#!/usr/bin/env python3
"""
Verify database connection and check if tables exist.

Usage:
    python -m extraction_service.scripts.verify_database
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from extraction_service.config import settings
from extraction_service.database.session import init_db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_connection():
    """Verify database connection and table existence."""
    try:
        # Initialize database session
        logger.info("="*80)
        logger.info("DATABASE VERIFICATION")
        logger.info("="*80)
        
        # Show connection details (masked password)
        db_url = settings.effective_database_url
        masked_url = db_url.split('@')[0].split(':')[:-1]
        host_part = db_url.split('@')[1] if '@' in db_url else 'unknown'
        logger.info(f"Database URL: postgresql://***:***@{host_part}")
        
        db_session = init_db(
            database_url=db_url,
            echo=False,
            pool_size=1,
            max_overflow=0
        )
        logger.info("✓ Database session initialized")
        
        # Try to connect and run queries
        async with db_session.get_session() as session:
            # Check database version
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✓ Connected to database: {version.split(',')[0]}")
            
            # Check if clinical_summaries table exists
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'clinical_summaries'
                )
            """))
            clinical_table_exists = result.scalar()
            
            if clinical_table_exists:
                logger.info("✓ clinical_summaries table EXISTS")
                
                # Get row count
                result = await session.execute(text("SELECT COUNT(*) FROM clinical_summaries"))
                count = result.scalar()
                logger.info(f"  Records in clinical_summaries: {count}")
                
                # Get table structure
                result = await session.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'clinical_summaries'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                logger.info("  Table structure:")
                for col in columns:
                    logger.info(f"    - {col[0]}: {col[1]}")
            else:
                logger.error("✗ clinical_summaries table DOES NOT EXIST")
                logger.info("\nTo create the table, run:")
                logger.info("  1. Manual SQL: Run the SQL from extraction_service/database/sql_schema/schema.sql")
                logger.info("  2. Or use SQLAlchemy: Base.metadata.create_all()")
            
            # Check if hospital_summaries table exists
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hospital_summaries'
                )
            """))
            hospital_table_exists = result.scalar()
            
            if hospital_table_exists:
                logger.info("✓ hospital_summaries table EXISTS")
                result = await session.execute(text("SELECT COUNT(*) FROM hospital_summaries"))
                count = result.scalar()
                logger.info(f"  Records in hospital_summaries: {count}")
            else:
                logger.warning("⚠ hospital_summaries table DOES NOT EXIST")
            
            # List all tables in the database
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            logger.info(f"\nAll tables in database ({len(tables)} total):")
            for table in tables:
                logger.info(f"  - {table[0]}")
        
        await db_session.close()
        logger.info("\n" + "="*80)
        logger.info("VERIFICATION COMPLETE")
        logger.info("="*80)
        
        return clinical_table_exists
        
    except Exception as e:
        logger.error(f"\n✗ Database connection failed: {e}", exc_info=True)
        logger.info("\nPossible issues:")
        logger.info("  1. Database credentials are incorrect")
        logger.info("  2. Database server is not accessible")
        logger.info("  3. Database does not exist")
        logger.info("\nCheck your .env file or environment variables:")
        logger.info("  - PG_HOSPITAL_HOST")
        logger.info("  - PG_HOSPITAL_PORT")
        logger.info("  - PG_HOSPITAL_DATABASE")
        logger.info("  - PG_HOSPITAL_USER")
        logger.info("  - PG_HOSPITAL_PASSWORD")
        return False


async def main():
    """Main execution."""
    try:
        table_exists = await verify_connection()
        sys.exit(0 if table_exists else 1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

