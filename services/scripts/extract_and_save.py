#!/usr/bin/env python3
"""
Unified extraction script that extracts both clinical and hospital summaries
from a single clinical document file and saves to both database tables.

Usage:
    python -m extraction_service.scripts.extract_and_save \\
        --file clinical_visits/P-027_document_2457.txt \\
        --patient-id P-027
"""

import argparse
import asyncio
import logging
import sys
import uuid
from pathlib import Path
from typing import Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from extraction_service.config import settings
from extraction_service.database.session import init_db
from extraction_service.extractors.clinical_summary_extractor import ClinicalSummaryExtractor
from extraction_service.extractors.hospital_summary_extractor import HospitalSummaryExtractor
from extraction_service.repositories.clinical_summary_repository import ClinicalSummaryRepository
from extraction_service.repositories.hospital_summary_repository import HospitalSummaryRepository
from extraction_service.core.exceptions import ExtractionError, DatabaseError

logger = logging.getLogger(__name__)


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


async def extract_parallel(
    patient_id: str,
    hospitalization_id: str,
    raw_text: str,
    clinical_extractor: ClinicalSummaryExtractor,
    hospital_extractor: HospitalSummaryExtractor
) -> Tuple[dict, dict]:
    """
    Extract both clinical and hospital summaries in parallel.
    
    Args:
        patient_id: Patient identifier
        hospitalization_id: Generated UUID for hospitalization
        raw_text: Clinical document text
        clinical_extractor: Clinical summary extractor instance
        hospital_extractor: Hospital summary extractor instance
        
    Returns:
        Tuple of (clinical_data, hospital_data) dictionaries
    """
    logger.info("Starting parallel extraction...")
    logger.info(f"Patient ID: {patient_id}")
    logger.info(f"Hospitalization ID: {hospitalization_id}")
    
    # Prepare metadata with generated hospitalization_id
    metadata = {
        "patient_id": patient_id,
        "hospitalization_id": hospitalization_id,
    }
    
    # Run both extractions in parallel
    # This will run 11 LLM tools total:
    # - Clinical: 8 tools in parallel
    # - Hospital: 3 tools (1 first, then 2 in parallel)
    try:
        clinical_data, hospital_data = await asyncio.gather(
            clinical_extractor.extract(patient_id, raw_text, metadata),
            hospital_extractor.extract(patient_id, raw_text, metadata)
        )
        
        logger.info("✓ Parallel extraction completed successfully")
        return clinical_data, hospital_data
        
    except Exception as e:
        logger.error(f"✗ Extraction failed: {e}", exc_info=True)
        raise ExtractionError(f"Failed to extract data: {e}") from e


async def save_to_database(
    db_session,
    patient_id: str,
    hospitalization_id: str,
    clinical_data: dict,
    hospital_data: dict
):
    """
    Save extracted data to both database tables.
    
    Args:
        db_session: Database session manager
        patient_id: Patient identifier
        hospitalization_id: Hospitalization identifier
        clinical_data: Extracted clinical summary data
        hospital_data: Extracted hospital summary data
        
    Returns:
        Tuple of (clinical_record, hospital_record)
    """
    logger.info("Saving to database...")
    
    try:
        async with db_session.get_session() as session:
            # Create repositories
            clinical_repo = ClinicalSummaryRepository(session)
            hospital_repo = HospitalSummaryRepository(session)
            
            # Override hospitalization_id in clinical data
            # The clinical extractor puts it in the "summary" Pydantic model's metadata
            if "summary" in clinical_data and hasattr(clinical_data["summary"], "metadata"):
                # Update the metadata with our generated hospitalization_id
                clinical_data["summary"].metadata.hospitalization_id = hospitalization_id
            
            # Override hospitalization_id in hospital data
            # The hospital extractor puts it in the "summary_card" Pydantic model
            if "summary_card" in hospital_data:
                # Create a new summary_card with updated hospitalization_id
                summary_card = hospital_data["summary_card"]
                hospital_data["summary_card"] = summary_card.model_copy(
                    update={"hospitalization_id": hospitalization_id}
                )
            
            # Save clinical summary
            logger.info("Saving clinical summary...")
            clinical_record = await clinical_repo.create(clinical_data)
            logger.info(f"✓ Clinical summary saved: ID={clinical_record.id}")
            
            # Save hospital summary
            logger.info("Saving hospital summary...")
            hospital_record = await hospital_repo.create(hospital_data)
            logger.info(f"✓ Hospital summary saved: ID={hospital_record.id}")
            
            return clinical_record, hospital_record
            
    except DatabaseError as e:
        logger.error(f"✗ Database error: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"✗ Unexpected error saving to database: {e}", exc_info=True)
        raise DatabaseError(f"Failed to save to database: {e}") from e


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Extract and save clinical and hospital summaries from a single document",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m extraction_service.scripts.extract_and_save \\
      --file clinical_visits/P-027_document_2457.txt \\
      --patient-id P-027
  
  python -m extraction_service.scripts.extract_and_save \\
      --file /path/to/document.txt \\
      --patient-id PAT-001 \\
      --log-level DEBUG
        """
    )
    
    parser.add_argument(
        '--file',
        type=Path,
        required=True,
        help='Path to clinical document file'
    )
    
    parser.add_argument(
        '--patient-id',
        required=True,
        help='Patient identifier'
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
    
    # Print header
    print("\n" + "="*80)
    print("UNIFIED EXTRACTION: Clinical + Hospital Summaries")
    print("="*80)
    print(f"File: {args.file}")
    print(f"Patient ID: {args.patient_id}")
    print("="*80 + "\n")
    
    # Validate file exists
    if not args.file.exists():
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    if not args.file.is_file():
        logger.error(f"Not a file: {args.file}")
        sys.exit(1)
    
    try:
        # Read file content
        logger.info(f"Reading file: {args.file}")
        raw_text = args.file.read_text(encoding='utf-8')
        logger.info(f"Loaded {len(raw_text)} characters")
        
        # Generate hospitalization_id (UUID)
        hospitalization_id = str(uuid.uuid4())
        logger.info(f"Generated hospitalization_id: {hospitalization_id}")
        
        # Initialize extractors
        logger.info("Initializing extractors...")
        clinical_extractor = ClinicalSummaryExtractor()
        hospital_extractor = HospitalSummaryExtractor()
        logger.info("✓ Extractors initialized")
        
        # Run parallel extraction
        clinical_data, hospital_data = await extract_parallel(
            patient_id=args.patient_id,
            hospitalization_id=hospitalization_id,
            raw_text=raw_text,
            clinical_extractor=clinical_extractor,
            hospital_extractor=hospital_extractor
        )
        
        # Initialize database
        logger.info("Initializing database connection...")
        db_session = init_db(
            database_url=settings.effective_database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow
        )
        logger.info("✓ Database connection initialized")
        
        # Save to database
        clinical_record, hospital_record = await save_to_database(
            db_session=db_session,
            patient_id=args.patient_id,
            hospitalization_id=hospitalization_id,
            clinical_data=clinical_data,
            hospital_data=hospital_data
        )
        
        # Print success summary
        print("\n" + "="*80)
        print("SUCCESS: Extraction and Save Complete")
        print("="*80)
        print(f"Patient ID: {args.patient_id}")
        print(f"Hospitalization ID: {hospitalization_id}")
        print(f"\nClinical Summary Record:")
        print(f"  - ID: {clinical_record.id}")
        print(f"  - Created: {clinical_record.created_at}")
        print(f"\nHospital Summary Record:")
        print(f"  - ID: {hospital_record.id}")
        print(f"  - Facility: {hospital_record.facility.get('facility_name', 'N/A') if hospital_record.facility else 'N/A'}")
        print(f"  - Length of Stay: {hospital_record.length_of_stay_days} days")
        print("="*80 + "\n")
        
        # Cleanup
        await db_session.close()
        logger.info("Database connection closed")
        
        sys.exit(0)
        
    except ExtractionError as e:
        logger.error(f"Extraction failed: {e}")
        print(f"\n✗ ERROR: Extraction failed - {e}\n")
        sys.exit(1)
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        print(f"\n✗ ERROR: Database error - {e}\n")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n✗ ERROR: Unexpected error - {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

