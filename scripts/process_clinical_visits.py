#!/usr/bin/env python3
"""
Batch process all clinical visit files and verify database saves.

Usage:
    python -m extraction_service.scripts.process_clinical_visits \\
        --clinical-visits-dir /path/to/clinical_visits \\
        --patient-id-prefix PAT
"""

import argparse
import asyncio
import sys
from pathlib import Path
import logging
from uuid import UUID

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from extraction_service.config import settings
from extraction_service.database.session import init_db
from extraction_service.services.extraction_service import ExtractionService
from extraction_service.core.exceptions import ExtractionError, DatabaseError


def setup_logging(log_level: str, log_file: str = None):
    """Configure logging."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


async def verify_database_save(service: ExtractionService, record_id: UUID, patient_id: str):
    """Verify that a record was saved to the database."""
    try:
        record = await service.get_record(
            table_name="clinical_summaries",
            record_id=record_id
        )
        
        if record:
            logger.info(f"✓ Verified: Record {record_id} found in database")
            logger.info(f"  Patient ID: {record.patient_id}")
            logger.info(f"  Created at: {record.created_at}")
            return True
        else:
            logger.error(f"✗ Failed: Record {record_id} NOT found in database")
            return False
    except Exception as e:
        logger.error(f"✗ Error verifying record: {e}")
        return False


async def process_file(service: ExtractionService, file_path: Path, patient_id: str):
    """Process a single clinical visit file."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing: {file_path.name}")
    logger.info(f"{'='*80}")
    
    try:
        # Read file content
        raw_text = file_path.read_text(encoding='utf-8')
        logger.info(f"Loaded {len(raw_text)} characters from {file_path.name}")
        
        # Process extraction
        result = await service.process(
            extractor_name='clinical_summary',
            patient_id=patient_id,
            raw_text=raw_text
        )
        
        logger.info(f"✓ Extraction successful for {file_path.name}")
        logger.info(f"  Record ID: {result.id}")
        logger.info(f"  Patient ID: {result.patient_id}")
        
        # Verify database save
        verified = await verify_database_save(service, result.id, patient_id)
        
        return {
            'file': file_path.name,
            'success': True,
            'record_id': str(result.id),
            'patient_id': result.patient_id,
            'verified': verified
        }
        
    except ExtractionError as e:
        logger.error(f"✗ Extraction failed for {file_path.name}: {e}")
        return {
            'file': file_path.name,
            'success': False,
            'error': str(e),
            'verified': False
        }
    except DatabaseError as e:
        logger.error(f"✗ Database error for {file_path.name}: {e}")
        return {
            'file': file_path.name,
            'success': False,
            'error': str(e),
            'verified': False
        }
    except Exception as e:
        logger.error(f"✗ Unexpected error for {file_path.name}: {e}", exc_info=True)
        return {
            'file': file_path.name,
            'success': False,
            'error': str(e),
            'verified': False
        }


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Batch process clinical visit files and verify database saves",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--clinical-visits-dir',
        type=Path,
        default=Path('/Users/claimsync/Desktop/Product/Jerimed/clinical_visits'),
        help='Directory containing clinical visit files'
    )
    
    parser.add_argument(
        '--patient-id-prefix',
        default='PAT',
        help='Prefix for patient IDs (default: PAT)'
    )
    
    parser.add_argument(
        '--extractor',
        default='clinical_summary',
        help='Extractor to use (default: clinical_summary)'
    )
    
    parser.add_argument(
        '--log-level',
        default=settings.log_level,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help=f'Logging level (default: {settings.log_level})'
    )
    
    parser.add_argument(
        '--log-file',
        type=Path,
        default=settings.log_file,
        help='Path to log file (default: console only)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    global logger
    logger = logging.getLogger(__name__)
    
    # Validate directory
    if not args.clinical_visits_dir.exists():
        logger.error(f"Directory not found: {args.clinical_visits_dir}")
        sys.exit(1)
    
    if not args.clinical_visits_dir.is_dir():
        logger.error(f"Not a directory: {args.clinical_visits_dir}")
        sys.exit(1)
    
    # Find all text files
    text_files = sorted(args.clinical_visits_dir.glob('*.txt'))
    
    if not text_files:
        logger.warning(f"No .txt files found in {args.clinical_visits_dir}")
        sys.exit(0)
    
    logger.info(f"Found {len(text_files)} clinical visit files to process")
    
    # Initialize database
    try:
        db_session = init_db(
            database_url=settings.effective_database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow
        )
        logger.info("Database connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.error("Please check your database configuration in .env file")
        sys.exit(1)
    
    # Create service
    service = ExtractionService(db_session)
    
    # Print header
    print("\n" + "="*80)
    print("CLINICAL VISITS BATCH PROCESSING")
    print("="*80)
    print(f"Directory: {args.clinical_visits_dir}")
    print(f"Files to process: {len(text_files)}")
    print(f"Extractor: {args.extractor}")
    print("="*80 + "\n")
    
    # Process all files
    results = []
    for i, file_path in enumerate(text_files, 1):
        # Generate patient ID from file name (use doc ID or file number)
        patient_id = f"{args.patient_id_prefix}-{i:03d}"
        
        logger.info(f"\n[{i}/{len(text_files)}] Processing {file_path.name}...")
        
        result = await process_file(service, file_path, patient_id)
        results.append(result)
    
    # Print summary
    print("\n" + "="*80)
    print("PROCESSING SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    verified = [r for r in successful if r.get('verified', False)]
    
    print(f"Total files processed: {len(results)}")
    print(f"Successful extractions: {len(successful)}")
    print(f"Failed extractions: {len(failed)}")
    print(f"Database verified: {len(verified)}/{len(successful)}")
    
    if successful:
        print(f"\n✓ Successfully processed files:")
        for r in successful:
            verified_status = "✓ Verified" if r.get('verified') else "✗ Not verified"
            print(f"  - {r['file']}: {verified_status} (Record ID: {r.get('record_id', 'N/A')})")
    
    if failed:
        print(f"\n✗ Failed files:")
        for r in failed:
            print(f"  - {r['file']}: {r.get('error', 'Unknown error')}")
    
    print("="*80 + "\n")
    
    # Cleanup
    await db_session.close()
    logger.info("Database connection closed")
    
    # Exit with error code if any failed
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

