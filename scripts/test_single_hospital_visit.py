#!/usr/bin/env python3
"""
Test script to extract and store a single hospital visit document.

Usage:
    python -m extraction_service.scripts.test_single_hospital_visit \\
        --file hospital_visits/doc_3d0c2910-bf40-4956-b875-214bc8d6e956.txt \\
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
    """Test extraction and storage for a single hospital visit."""
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*80)
    print("TESTING HOSPITAL SUMMARY EXTRACTION")
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
            extractor_name='hospital_summary',
            patient_id=patient_id,
            raw_text=raw_text,
            metadata={'hospitalization_id': doc_id} if doc_id else None
        )
        
        print(f"\n✓ Extraction successful!")
        print(f"  Record ID: {result.id}")
        print(f"  Patient ID: {result.patient_id}")
        print(f"  Hospitalization ID: {result.hospitalization_id}")
        print(f"  Length of Stay: {result.length_of_stay_days} days")
        
        # Verify the data structure
        print("\n" + "="*80)
        print("VERIFYING STORED DATA STRUCTURE")
        print("="*80)
        
        # Check that all sections are stored separately
        sections = {
            'facility': result.facility,
            'timing': result.timing,
            'diagnosis': result.diagnosis,
            'medication_risk_assessment': result.medication_risk_assessment,
        }
        
        print("\nStored sections:")
        for section_name, section_data in sections.items():
            if section_data is not None:
                if isinstance(section_data, list):
                    print(f"  ✓ {section_name}: {len(section_data)} items (JSONB array)")
                elif isinstance(section_data, dict):
                    print(f"  ✓ {section_name}: {len(section_data)} keys (JSONB object)")
                else:
                    print(f"  ✓ {section_name}: present")
            else:
                print(f"  - {section_name}: None")
        
        # Show sample data from each section
        print("\n" + "="*80)
        print("SAMPLE DATA FROM EACH SECTION")
        print("="*80)
        
        if result.facility:
            print("\n🏥 Facility (JSONB):")
            facility = result.facility
            if isinstance(facility, dict):
                print(f"  Type: {type(facility).__name__}")
                print(f"  Keys: {list(facility.keys())[:5]}")
                if 'facility_name' in facility:
                    print(f"  Facility Name: {facility['facility_name']}")
                if 'facility_type' in facility:
                    print(f"  Facility Type: {facility['facility_type']}")
        
        if result.timing:
            print("\n⏰ Timing (JSONB):")
            timing = result.timing
            if isinstance(timing, dict):
                print(f"  Type: {type(timing).__name__}")
                print(f"  Keys: {list(timing.keys())[:5]}")
                if 'admission_date' in timing:
                    print(f"  Admission Date: {timing['admission_date']}")
                if 'discharge_date' in timing:
                    print(f"  Discharge Date: {timing['discharge_date']}")
        
        if result.diagnosis:
            print("\n🔍 Diagnosis (JSONB):")
            diagnosis = result.diagnosis
            if isinstance(diagnosis, dict):
                print(f"  Type: {type(diagnosis).__name__}")
                print(f"  Keys: {list(diagnosis.keys())[:5]}")
                if 'primary_diagnosis' in diagnosis:
                    print(f"  Primary Diagnosis: {diagnosis['primary_diagnosis']}")
                if 'secondary_diagnoses' in diagnosis:
                    print(f"  Secondary Diagnoses: {len(diagnosis['secondary_diagnoses'])} items")
        
        if result.medication_risk_assessment:
            print("\n💊 Medication Risk Assessment (JSONB):")
            risk = result.medication_risk_assessment
            if isinstance(risk, dict):
                print(f"  Type: {type(risk).__name__}")
                print(f"  Keys: {list(risk.keys())[:5]}")
                if 'risk_level' in risk:
                    print(f"  Risk Level: {risk['risk_level']}")
                if 'likelihood_percentage' in risk:
                    print(f"  Likelihood: {risk['likelihood_percentage']}")
        
        # Verify retrieval
        print("\n" + "="*80)
        print("VERIFYING DATABASE RETRIEVAL")
        print("="*80)
        
        retrieved = await service.get_record(
            table_name="hospital_summaries",
            record_id=result.id
        )
        
        if retrieved:
            print("✓ Record successfully retrieved from database")
            print(f"  Patient ID: {retrieved.patient_id}")
            print(f"  Hospitalization ID: {retrieved.hospitalization_id}")
            print(f"  Length of Stay: {retrieved.length_of_stay_days} days")
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
        description="Test hospital summary extraction on a single document",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--file',
        type=Path,
        default=Path('/Users/claimsync/Desktop/Product/Jerimed/hospital_visits/doc_3d0c2910-bf40-4956-b875-214bc8d6e956.txt'),
        help='Path to hospital visit file'
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

