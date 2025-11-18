#!/usr/bin/env python3
"""
Test script to verify the extraction service end-to-end.

This script tests:
1. Database connection
2. Extractor registration
3. Complete extraction pipeline
4. Data storage and retrieval
5. Pydantic model conversion
"""

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
from extraction_service.core.registry import registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample clinical text for testing
SAMPLE_CLINICAL_TEXT = """
DOC_ID:test-123-456-789

FACILITY: Memorial Regional Hospital
123 Main Street, Springfield, IL 62701

PATIENT: John Doe
MRN: TEST-PAT-001

ADMISSION DATE: January 15, 2024 at 14:30
DISCHARGE DATE: January 20, 2024 at 10:00
ADMISSION SOURCE: Emergency Department
DISCHARGE DISPOSITION: Home with home health services

PRIMARY DIAGNOSIS: Acute myocardial infarction (STEMI)
ICD-10: I21.3

SECONDARY DIAGNOSES:
- Type 2 diabetes mellitus (E11.9)
- Hypertension (I10)
- Chronic kidney disease, stage 3 (N18.3)

MEDICATIONS ON ADMISSION:
- Metformin 1000mg BID
- Lisinopril 10mg daily
- Atorvastatin 40mg daily

HOSPITAL COURSE:
Patient presented with acute chest pain radiating to left arm. 
Troponin elevated at 5.2. Underwent emergent cardiac catheterization 
with stent placement to LAD. Post-procedure course complicated by 
acute kidney injury with creatinine rising from baseline 1.4 to 2.8. 
Metformin was discontinued due to AKI risk.

DISCHARGE MEDICATIONS:
- Aspirin 81mg daily
- Clopidogrel 75mg daily
- Atorvastatin 80mg daily (increased dose)
- Lisinopril 10mg daily
- Metoprolol 25mg BID (new)
"""


async def test_database_connection():
    """Test 1: Database connection."""
    print("\n" + "="*80)
    print("TEST 1: Database Connection")
    print("="*80)
    
    try:
        db_session = init_db(
            database_url=settings.database_url,
            echo=False,
            pool_size=1,
            max_overflow=0
        )
        
        # Try to get a session
        async with db_session.get_session() as session:
            pass
        
        print("✓ Database connection successful")
        await db_session.close()
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


async def test_extractor_registration():
    """Test 2: Extractor registration."""
    print("\n" + "="*80)
    print("TEST 2: Extractor Registration")
    print("="*80)
    
    try:
        # Import extractors (triggers auto-registration)
        from extraction_service.extractors import HospitalSummaryExtractor
        
        # Check registry
        extractors = registry.list_all()
        
        print(f"Registered extractors: {len(extractors)}")
        for name, extractor in extractors.items():
            print(f"  - {name}: {extractor.table_name} (v{extractor.version})")
        
        if 'hospital_summary' in extractors:
            print("✓ Hospital summary extractor registered")
            return True
        else:
            print("✗ Hospital summary extractor not found")
            return False
        
    except Exception as e:
        print(f"✗ Extractor registration test failed: {e}")
        return False


async def test_extraction_pipeline():
    """Test 3: Complete extraction and storage pipeline."""
    print("\n" + "="*80)
    print("TEST 3: Extraction and Storage Pipeline")
    print("="*80)
    
    try:
        # Initialize database
        db_session = init_db(settings.database_url, echo=False)
        
        # Create service
        service = ExtractionService(db_session)
        
        # Process extraction
        print("Running extraction...")
        result = await service.process(
            extractor_name="hospital_summary",
            patient_id="TEST-PAT-001",
            raw_text=SAMPLE_CLINICAL_TEXT
        )
        
        print(f"\n✓ Extraction successful!")
        print(f"  Record ID: {result.id}")
        print(f"  Hospitalization ID: {result.hospitalization_id}")
        print(f"  Patient ID: {result.patient_id}")
        
        # Cleanup
        await db_session.close()
        
        return True, result.id
        
    except Exception as e:
        print(f"✗ Extraction pipeline failed: {e}")
        logger.error("Extraction failed", exc_info=True)
        return False, None


async def test_data_retrieval(record_id):
    """Test 4: Data retrieval and Pydantic conversion."""
    print("\n" + "="*80)
    print("TEST 4: Data Retrieval and Pydantic Conversion")
    print("="*80)
    
    try:
        # Initialize database
        db_session = init_db(settings.database_url, echo=False)
        
        # Create service
        service = ExtractionService(db_session)
        
        # Retrieve by ID
        print(f"Retrieving record {record_id}...")
        result = await service.get_record(
            table_name="hospital_summaries",
            record_id=record_id
        )
        
        if not result:
            print("✗ Record not found")
            return False
        
        print(f"✓ Record retrieved successfully")
        
        # Test Pydantic model access
        print("\nTesting Pydantic model access:")
        print(f"  Facility name: {result.facility.facility_name}")
        print(f"  Facility type: {result.facility.facility_type}")
        print(f"  Admission date: {result.timing.admission_date}")
        print(f"  Length of stay: {result.length_of_stay_days} days")
        print(f"  Primary diagnosis: {result.diagnosis.primary_diagnosis}")
        print(f"  Risk level: {result.medication_risk_assessment.risk_level}")
        
        # Verify types
        from extraction_service.hospital_admission_summary_card.facility_timing.model import FacilityData
        from extraction_service.hospital_admission_summary_card.diagnosis.model import DiagnosisData
        
        assert isinstance(result.facility, FacilityData), "facility is not FacilityData"
        assert isinstance(result.diagnosis, DiagnosisData), "diagnosis is not DiagnosisData"
        
        print("\n✓ Pydantic models correctly deserialized from JSONB")
        
        # Cleanup
        await db_session.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Data retrieval test failed: {e}")
        logger.error("Retrieval failed", exc_info=True)
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("EXTRACTION SERVICE - END-TO-END TESTS")
    print("="*80)
    print(f"Database URL: {settings.database_url}")
    print("="*80)
    
    results = []
    
    # Test 1: Database connection
    result = await test_database_connection()
    results.append(("Database Connection", result))
    if not result:
        print("\n✗ Cannot continue without database connection")
        sys.exit(1)
    
    # Test 2: Extractor registration
    result = await test_extractor_registration()
    results.append(("Extractor Registration", result))
    if not result:
        print("\n✗ Cannot continue without extractors")
        sys.exit(1)
    
    # Test 3: Extraction pipeline
    result, record_id = await test_extraction_pipeline()
    results.append(("Extraction Pipeline", result))
    if not result:
        print("\n✗ Extraction pipeline failed")
        sys.exit(1)
    
    # Test 4: Data retrieval
    result = await test_data_retrieval(record_id)
    results.append(("Data Retrieval", result))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("="*80)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("="*80 + "\n")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        print("="*80 + "\n")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

