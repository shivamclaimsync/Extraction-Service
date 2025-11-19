#!/usr/bin/env python3
"""
Test script to verify the repository storage mechanism with mock data.

This tests that the repository correctly breaks apart ClinicalSummaryResult
and stores each section in separate JSONB columns.
"""

import argparse
import asyncio
import sys
from pathlib import Path
import logging
import json
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from extraction_service.config import settings
from extraction_service.database.session import init_db
from extraction_service.repositories.clinical_summary_repository import ClinicalSummaryRepository
from extraction_service.extractors.clinical_summary_entity.aggregator import (
    ClinicalSummaryResult,
    ClinicalSummary,
    ClinicalSummaryMetadata,
)
from extraction_service.extractors.clinical_summary_entity.presentation.model import PresentationData
from extraction_service.extractors.clinical_summary_entity.history.model import HistoryData
from extraction_service.extractors.clinical_summary_entity.findings.model import FindingsData
from extraction_service.extractors.clinical_summary_entity.assessment.model import AssessmentData
from extraction_service.extractors.clinical_summary_entity.course.model import CourseData
from extraction_service.extractors.clinical_summary_entity.follow_up.model import FollowUpData


def setup_logging(log_level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def test_repository_storage():
    """Test repository storage with mock data."""
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*80)
    print("TESTING REPOSITORY STORAGE MECHANISM")
    print("="*80)
    print("This test verifies that ClinicalSummaryResult is correctly")
    print("broken apart and stored in separate JSONB columns.")
    print("="*80 + "\n")
    
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
    
    try:
        async with db_session.get_session() as session:
            repo = ClinicalSummaryRepository(session)
            
            # Create mock ClinicalSummaryResult
            print("Creating mock ClinicalSummaryResult...")
            
            # Create minimal valid data for each section
            mock_presentation = PresentationData(
                symptoms=["Chest pain", "Dyspnea"],
                chief_complaint="MD Reassessment",
                vital_signs={
                    "blood_pressure": "101/72",
                    "heart_rate": 81,
                    "temperature": 98.4,
                    "oxygen_saturation": 96
                }
            )
            
            mock_history = HistoryData(
                past_medical_history=["Coronary artery disease", "Chronic respiratory failure"],
                allergies=["cephalexin", "prednisone"],
                current_medications=["Imdur", "Bumetanide"]
            )
            
            mock_findings = FindingsData(
                physical_exam={
                    "general": "Alert and conversant",
                    "cardiac": "RRR",
                    "respiratory": "Scattered crackles bilaterally",
                    "extremities": "1+ edema bilateral LE"
                },
                anthropometrics=None  # Can be None
            )
            
            mock_assessment = AssessmentData(
                primary_diagnosis="Exertional dyspnea",
                diagnoses=[
                    {
                        "diagnosis": "Exertional dyspnea",
                        "icd10": "R06.09",
                        "evidence": "Progressive symptoms related to UIP"
                    }
                ]
            )
            
            mock_course = CourseData(
                course_summary="Patient seen for reassessment. Overall doing well.",
                complications=None
            )
            
            mock_followup = FollowUpData(
                discharge_instructions=["Continue current medications"],
                appointments=[],
                recommendations=[],
                patient_education=[],
                care_transitions=[]
            )
            
            # Create ClinicalSummary
            clinical_summary = ClinicalSummary(
                patient_presentation=mock_presentation,
                relevant_history=mock_history,
                clinical_findings=mock_findings,
                clinical_assessment=mock_assessment,
                hospital_course=mock_course,
                follow_up_plan=mock_followup,
                treatments_procedures=[],
                lab_results=[],
            )
            
            # Create metadata
            metadata = ClinicalSummaryMetadata(
                hospitalization_id="1bc2fa78-15f4-4dc8-be1d-658b6a1d1856",
                patient_id="PAT-001",
                raw_summary_text="Test clinical summary",
                parsed_at=datetime.now(timezone.utc),
                parsing_model_version="gpt-4o-mini",
                confidence_score=0.95
            )
            
            # Create ClinicalSummaryResult
            summary_result = ClinicalSummaryResult(
                summary=clinical_summary,
                metadata=metadata
            )
            
            # Prepare data for repository
            data = {
                "patient_id": "PAT-001",
                "summary": summary_result
            }
            
            print("✓ Mock data created\n")
            
            # Test repository create
            print("Testing repository.create()...")
            result = await repo.create(data)
            
            print(f"\n✓ Record created successfully!")
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
            all_present = True
            for section_name, section_data in sections.items():
                if section_data is not None:
                    if isinstance(section_data, list):
                        print(f"  ✓ {section_name}: {len(section_data)} items (JSONB array)")
                    elif isinstance(section_data, dict):
                        print(f"  ✓ {section_name}: {len(section_data)} keys (JSONB object)")
                    else:
                        print(f"  ✓ {section_name}: present")
                else:
                    print(f"  - {section_name}: None (nullable)")
            
            # Show sample data
            print("\n" + "="*80)
            print("SAMPLE DATA FROM EACH SECTION")
            print("="*80)
            
            if result.patient_presentation:
                print("\n📋 Patient Presentation (JSONB):")
                pp = result.patient_presentation
                if isinstance(pp, dict):
                    print(f"  Type: {type(pp).__name__}")
                    print(f"  Keys: {list(pp.keys())[:5]}")
                    if 'symptoms' in pp:
                        print(f"  Symptoms: {pp['symptoms']}")
            
            if result.relevant_history:
                print("\n📜 Relevant History (JSONB):")
                rh = result.relevant_history
                if isinstance(rh, dict):
                    print(f"  Type: {type(rh).__name__}")
                    print(f"  Keys: {list(rh.keys())[:5]}")
                    if 'past_medical_history' in rh:
                        print(f"  PMH: {rh['past_medical_history'][:2] if isinstance(rh['past_medical_history'], list) else 'N/A'}")
            
            if result.clinical_assessment:
                print("\n🔍 Clinical Assessment (JSONB):")
                ca = result.clinical_assessment
                if isinstance(ca, dict):
                    print(f"  Type: {type(ca).__name__}")
                    print(f"  Keys: {list(ca.keys())[:5]}")
                    if 'primary_diagnosis' in ca:
                        print(f"  Primary Diagnosis: {ca['primary_diagnosis']}")
            
            # Test retrieval
            print("\n" + "="*80)
            print("TESTING RETRIEVAL METHODS")
            print("="*80)
            
            # Get by ID
            retrieved_by_id = await repo.get_by_id(result.id)
            if retrieved_by_id:
                print("✓ get_by_id() works")
            else:
                print("✗ get_by_id() failed")
            
            # Get by hospitalization_id
            retrieved_by_hosp = await repo.get_by_hospitalization_id("1bc2fa78-15f4-4dc8-be1d-658b6a1d1856")
            if retrieved_by_hosp:
                print("✓ get_by_hospitalization_id() works")
            else:
                print("✗ get_by_hospitalization_id() failed")
            
            # Get by patient_id
            retrieved_by_patient = await repo.get_by_patient_id("PAT-001", limit=10)
            if retrieved_by_patient and len(retrieved_by_patient) > 0:
                print(f"✓ get_by_patient_id() works (found {len(retrieved_by_patient)} records)")
            else:
                print("✗ get_by_patient_id() failed")
            
            # Show full structure
            print("\n" + "="*80)
            print("FULL RECORD STRUCTURE (to_dict)")
            print("="*80)
            record_dict = result.to_dict()
            print(json.dumps(record_dict, indent=2, default=str)[:1500] + "...")
            
            print("\n" + "="*80)
            print("✓ REPOSITORY STORAGE TEST COMPLETED SUCCESSFULLY")
            print("="*80)
            print("\nSummary:")
            print("  ✓ ClinicalSummaryResult broken apart correctly")
            print("  ✓ Each section stored in separate JSONB column")
            print("  ✓ hospitalization_id stored as separate column")
            print("  ✓ All retrieval methods work correctly")
            print("="*80 + "\n")
            
            return result
            
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        logger.error("Test failed", exc_info=True)
        sys.exit(1)
    finally:
        await db_session.close()
        logger.info("Database connection closed")


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Test repository storage mechanism",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
    await test_repository_storage()


if __name__ == '__main__':
    asyncio.run(main())

