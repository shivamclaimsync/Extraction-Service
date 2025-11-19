#!/usr/bin/env python3
"""
Create the clinical_summaries table in the database.

Usage:
    python -m extraction_service.scripts.create_clinical_summaries_table
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from extraction_service.config import settings
from extraction_service.database.session import init_db
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_table():
    """Create the clinical_summaries table."""
    # Read the SQL schema
    schema_file = Path(__file__).parent.parent / "database" / "sql_schema" / "schema.sql"
    
    with open(schema_file, 'r') as f:
        schema_sql = f.read()
    
    # Extract only the clinical_summaries table creation part
    start_marker = "-- Clinical summaries table"
    end_marker = "-- Example queries for clinical_summaries"
    
    start_idx = schema_sql.find(start_marker)
    end_idx = schema_sql.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        logger.error("Could not find clinical_summaries table definition in schema.sql")
        return False
    
    create_table_sql = schema_sql[start_idx:end_idx].strip()
    
    # Get database URL and parse it
    db_url = settings.effective_database_url
    
    # Parse the URL (postgresql+asyncpg://user:pass@host:port/dbname)
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Connect directly with asyncpg to run DDL
    try:
        # Parse connection string
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
        if not match:
            logger.error(f"Could not parse database URL: {db_url}")
            return False
        
        user, password, host, port, database = match.groups()
        
        logger.info(f"Connecting to database: {host}:{port}/{database}")
        
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database
        )
        
        logger.info("Connected to database")
        
        # Execute the CREATE TABLE statement
        await conn.execute(create_table_sql)
        
        logger.info("✓ Successfully created clinical_summaries table")
        
        # Verify table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'clinical_summaries'
            )
        """)
        
        if table_exists:
            logger.info("✓ Verified: clinical_summaries table exists")
        else:
            logger.warning("⚠ Table creation reported success but table not found")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create table: {e}", exc_info=True)
        return False


async def main():
    """Main execution."""
    try:
        success = await create_table()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

