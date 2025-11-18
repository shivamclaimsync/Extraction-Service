#!/usr/bin/env python3
"""
Manual extraction script for processing clinical notes.

Usage:
    python -m extraction_service.scripts.run_extraction \\
        --patient-id PAT-123 \\
        --text-file /path/to/clinical_note.txt \\
        --extractor hospital_summary
"""

import argparse
import asyncio
import sys
from pathlib import Path
import logging

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


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Extract structured data from clinical notes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from file
  python -m extraction_service.scripts.run_extraction \\
      --patient-id PAT-123 \\
      --text-file note.txt

  # Extract with inline text
  python -m extraction_service.scripts.run_extraction \\
      --patient-id PAT-456 \\
      --text "Patient admitted on..."

  # Use specific extractor
  python -m extraction_service.scripts.run_extraction \\
      --patient-id PAT-789 \\
      --text-file note.txt \\
      --extractor hospital_summary
        """
    )
    
    parser.add_argument(
        '--patient-id',
        required=True,
        help='Patient identifier'
    )
    
    parser.add_argument(
        '--text-file',
        type=Path,
        help='Path to clinical note text file'
    )
    
    parser.add_argument(
        '--text',
        help='Clinical note text (inline)'
    )
    
    parser.add_argument(
        '--extractor',
        default='hospital_summary',
        help='Extractor to use (default: hospital_summary)'
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
    
    parser.add_argument(
        '--output-format',
        choices=['summary', 'json', 'full'],
        default='summary',
        help='Output format (default: summary)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    # Validate input
    if not args.text_file and not args.text:
        logger.error("Must provide either --text-file or --text")
        sys.exit(1)
    
    # Read clinical text
    if args.text_file:
        if not args.text_file.exists():
            logger.error(f"File not found: {args.text_file}")
            sys.exit(1)
        
        try:
            raw_text = args.text_file.read_text()
            logger.info(f"Loaded clinical text from {args.text_file} ({len(raw_text)} chars)")
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            sys.exit(1)
    else:
        raw_text = args.text
    
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
        sys.exit(1)
    
    # Create service
    service = ExtractionService(db_session)
    
    # Print header
    print("\n" + "="*80)
    print("EXTRACTION SERVICE")
    print("="*80)
    print(f"Patient ID: {args.patient_id}")
    print(f"Extractor: {args.extractor}")
    print(f"Text length: {len(raw_text)} characters")
    print("="*80 + "\n")
    
    try:
        # Process extraction
        logger.info(f"Starting extraction for patient {args.patient_id}")
        
        result = await service.process(
            extractor_name=args.extractor,
            patient_id=args.patient_id,
            raw_text=raw_text
        )
        
        # Print results
        print("✓ EXTRACTION SUCCESSFUL\n")
        
        if args.output_format == 'summary':
            print(f"Record ID: {result.id}")
            print(f"Hospitalization ID: {result.hospitalization_id}")
            print(f"Patient ID: {result.patient_id}")
            print(f"\nFacility:")
            print(f"  Name: {result.facility.facility_name}")
            print(f"  Type: {result.facility.facility_type}")
            if result.facility.address:
                print(f"  City: {result.facility.address.city}")
                print(f"  State: {result.facility.address.state}")
            print(f"\nTiming:")
            print(f"  Admission: {result.timing.admission_date}")
            print(f"  Discharge: {result.timing.discharge_date}")
            print(f"  Length of stay: {result.length_of_stay_days} days")
            print(f"\nDiagnosis:")
            print(f"  Primary: {result.diagnosis.primary_diagnosis}")
            if result.diagnosis.primary_diagnosis_icd10:
                print(f"  ICD-10: {result.diagnosis.primary_diagnosis_icd10}")
            print(f"  Category: {result.diagnosis.diagnosis_category}")
            print(f"  Secondary diagnoses: {len(result.diagnosis.secondary_diagnoses)}")
            print(f"\nMedication Risk:")
            print(f"  Risk level: {result.medication_risk_assessment.risk_level}")
            print(f"  Likelihood: {result.medication_risk_assessment.likelihood_percentage.percentage}%")
            print(f"  Confidence: {result.medication_risk_assessment.confidence_score:.2f}")
            print(f"  Risk factors: {len(result.medication_risk_assessment.risk_factors)}")
        
        elif args.output_format == 'json':
            import json
            print(json.dumps(result.to_dict(), indent=2, default=str))
        
        elif args.output_format == 'full':
            print(result)
        
        print(f"\n{'='*80}")
        print("Extraction completed successfully")
        print(f"{'='*80}\n")
        
        logger.info("Extraction completed successfully")
        
    except ExtractionError as e:
        logger.error(f"Extraction failed: {e}")
        print(f"\n✗ EXTRACTION FAILED", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        print(f"\n✗ DATABASE ERROR", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n✗ UNEXPECTED ERROR", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    finally:
        # Cleanup
        await db_session.close()
        logger.info("Database connection closed")


if __name__ == '__main__':
    asyncio.run(main())

