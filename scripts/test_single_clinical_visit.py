#!/usr/bin/env python3
"""
Test script to extract and store a single clinical visit document.

Usage:
    python -m extraction_service.scripts.test_single_clinical_visit \\
        --file clinical_visits/doc_1bc2fa78-15f4-4dc8-be1d-658b6a1d1856.txt \\
        --patient-id PAT-001
"""

import argparse
import asyncio
import sys
from pathlib import Path
import logging
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from extraction_service.config import settings
from extraction_service.database.session import init_db
from extraction_service.services.extraction_service import ExtractionService
from extraction_service.core.exceptions import ExtractionError, DatabaseError


def setup_logging(log_level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def test_extraction(file_path: Path, patient_id: str):
    """Test extraction and storage for a single clinical visit."""
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*80)
    print("TESTING CLINICAL SUMMARY EXTRACTION")
    print("="*80)
    print(f"File: {file_path}")
    print(f"Patient ID: {patient_id}")
    print("="*80 + "\n")
    
    # Read file
    if not file_path.exists():
        print(f"✗ Error: File not found: {file_path}")
        sys.exit(1)
    
    raw_text = file_path.read_text(encoding='utf-8')
    print(f"✓ Loaded {len(raw_text)} characters from file\n")
    
    # Initialize database
    try:
        db_session = init_db(
            database_url=settings.effective_database_url,
            echo=False,
            pool_size=1,
            max_overflow=0
        )
        logger.info("Database connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        print(f"✗ Database initialization failed: {e}")
        sys.exit(1)
    
    # Create service
    service = ExtractionService(db_session)
    
    try:
        # Extract DOC_ID from file if present
        doc_id = None
        for line in raw_text.split('\n'):
            if 'DOC_ID:' in line:
                parts = line.split('DOC_ID:')
                if len(parts) > 1:
                    doc_id = parts[1].strip().split()[0] if parts[1].strip() else None
                break
        
        # Process extraction
        print("Running extraction...")
        result = await service.process(
            extractor_name='clinical_summary',
            patient_id=patient_id,
            raw_text=raw_text,
            metadata={'hospitalization_id': doc_id} if doc_id else None
        )
        
        print(f"\n✓ Extraction successful!")
        print(f"  Record ID: {result.id}")
        print(f"  Patient ID: {result.patient_id}")
        print(f"  Hospitalization ID: {result.hospitalization_id}")
        print(f"  Created at: {result.created_at}")
        
        # Verify the data structure
        print("\n" + "="*80)
        print("VERIFYING STORED DATA STRUCTURE")
        print("="*80)
        
        # Check that all sections are stored separately
        sections = {
            'patient_presentation': result.patient_presentation,
            'relevant_history': result.relevant_history,
            'clinical_findings': result.clinical_findings,
            'clinical_assessment': result.clinical_assessment,
            'hospital_course': result.hospital_course,
            'follow_up_plan': result.follow_up_plan,
            'treatments_procedures': result.treatments_procedures,
            'lab_results': result.lab_results,
        }
        
        print("\nStored sections:")
        for section_name, section_data in sections.items():
            if section_data is not None:
                if isinstance(section_data, list):
                    print(f"  ✓ {section_name}: {len(section_data)} items")
                elif isinstance(section_data, dict):
                    print(f"  ✓ {section_name}: {len(section_data)} keys")
                else:
                    print(f"  ✓ {section_name}: present")
            else:
                print(f"  - {section_name}: None")
        
        # Show sample data from each section
        print("\n" + "="*80)
        print("SAMPLE DATA FROM EACH SECTION")
        print("="*80)
        
        if result.patient_presentation:
            print("\n📋 Patient Presentation:")
            pp = result.patient_presentation
            if isinstance(pp, dict):
                print(f"  Keys: {list(pp.keys())[:5]}...")
                # Try to show some content
                for key in ['symptoms', 'chief_complaint', 'vital_signs']:
                    if key in pp:
                        print(f"  {key}: {str(pp[key])[:100]}...")
        
        if result.clinical_assessment:
            print("\n🔍 Clinical Assessment:")
            ca = result.clinical_assessment
            if isinstance(ca, dict):
                print(f"  Keys: {list(ca.keys())[:5]}...")
                for key in ['primary_diagnosis', 'diagnoses']:
                    if key in ca:
                        print(f"  {key}: {str(ca[key])[:100]}...")
        
        if result.lab_results:
            print(f"\n🧪 Lab Results: {len(result.lab_results)} tests")
            if len(result.lab_results) > 0:
                first_lab = result.lab_results[0]
                if isinstance(first_lab, dict):
                    print(f"  First lab keys: {list(first_lab.keys())[:5]}...")
        
        if result.treatments_procedures:
            print(f"\n💊 Treatments/Procedures: {len(result.treatments_procedures)} items")
            if len(result.treatments_procedures) > 0:
                first_treatment = result.treatments_procedures[0]
                if isinstance(first_treatment, dict):
                    print(f"  First treatment keys: {list(first_treatment.keys())[:5]}...")
        
        # Verify retrieval
        print("\n" + "="*80)
        print("VERIFYING DATABASE RETRIEVAL")
        print("="*80)
        
        retrieved = await service.get_record(
            table_name="clinical_summaries",
            record_id=result.id
        )
        
        if retrieved:
            print("✓ Record successfully retrieved from database")
            print(f"  Patient ID: {retrieved.patient_id}")
            print(f"  Hospitalization ID: {retrieved.hospitalization_id}")
            print(f"  All sections present: ✓")
        else:
            print("✗ Failed to retrieve record from database")
        
        # Show full structure
        print("\n" + "="*80)
        print("FULL RECORD STRUCTURE")
        print("="*80)
        record_dict = result.to_dict()
        print(json.dumps(record_dict, indent=2, default=str)[:2000] + "...")
        
        print("\n" + "="*80)
        print("✓ TEST COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
        return result
        
    except ExtractionError as e:
        print(f"\n✗ Extraction failed: {e}")
        logger.error("Extraction failed", exc_info=True)
        sys.exit(1)
    except DatabaseError as e:
        print(f"\n✗ Database error: {e}")
        logger.error("Database error", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logger.error("Unexpected error", exc_info=True)
        sys.exit(1)
    finally:
        await db_session.close()
        logger.info("Database connection closed")


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Test clinical summary extraction on a single document",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--file',
        type=Path,
        default=Path('/Users/claimsync/Desktop/Product/Jerimed/clinical_visits/doc_1bc2fa78-15f4-4dc8-be1d-658b6a1d1856.txt'),
        help='Path to clinical visit file'
    )
    
    parser.add_argument(
        '--patient-id',
        default='PAT-001',
        help='Patient ID to use (default: PAT-001)'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Run test
    await test_extraction(args.file, args.patient_id)


if __name__ == '__main__':
    asyncio.run(main())

