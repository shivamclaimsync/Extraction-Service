"""Main extraction service that orchestrates extraction and storage."""

from typing import Dict, Any, Optional
from uuid import UUID
import logging

from extraction_service.core.exceptions import ExtractionError, DatabaseError
from extraction_service.core.registry import registry
from extraction_service.database.session import DatabaseSession
from extraction_service.models.hospital_summary_db import HospitalSummary
from extraction_service.models.clinical_summary_db import ClinicalSummary
from extraction_service.repositories.hospital_summary_repository import HospitalSummaryRepository
from extraction_service.repositories.clinical_summary_repository import ClinicalSummaryRepository

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Main service for extraction pipeline.
    
    Orchestrates:
    1. Getting the appropriate extractor from registry
    2. Running extraction on clinical text
    3. Storing results in database
    """
    
    def __init__(self, db_session: DatabaseSession):
        """
        Initialize extraction service.
        
        Args:
            db_session: DatabaseSession instance for database operations
        """
        self.db_session = db_session
        self.registry = registry
        
        logger.info("Extraction service initialized")
    
    async def process(
        self,
        extractor_name: str,
        patient_id: str,
        raw_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HospitalSummary | ClinicalSummary:
        """
        Complete extraction and storage pipeline.
        
        Args:
            extractor_name: Name of extractor to use (e.g., 'hospital_summary')
            patient_id: Patient identifier
            raw_text: Raw clinical text to extract from
            metadata: Optional metadata dictionary
            
        Returns:
            Saved database record (SQLAlchemy model)
            
        Raises:
            ValueError: If extractor not found
            ExtractionError: If extraction fails
            DatabaseError: If database operation fails
        """
        # Get extractor from registry
        extractor = self.registry.get(extractor_name)
        if not extractor:
            available = ", ".join(self.registry.list_names())
            raise ValueError(
                f"Extractor '{extractor_name}' not found. "
                f"Available extractors: {available}"
            )
        
        logger.info(
            f"Processing extraction: extractor={extractor_name}, "
            f"patient_id={patient_id}"
        )
        
        try:
            # Step 1: Extract data using LLM (this can take a while)
            extraction_data = await extractor.extract(
                patient_id=patient_id,
                raw_text=raw_text,
                metadata=metadata
            )
            
            logger.info(f"Extraction successful for patient {patient_id}")
            
            # Step 2: Save to database (create fresh session after LLM extraction)
            async with self.db_session.get_session() as session:
                # Get appropriate repository based on table name
                if extractor.table_name == "hospital_summaries":
                    repo = HospitalSummaryRepository(session)
                elif extractor.table_name == "clinical_summaries":
                    repo = ClinicalSummaryRepository(session)
                else:
                    raise ValueError(
                        f"No repository configured for table: {extractor.table_name}"
                    )
                
                # Create record
                db_record = await repo.create(extraction_data)
            
            logger.info(
                f"Successfully saved {extractor.table_name} record: {db_record.id}"
            )
            
            return db_record
            
        except ExtractionError:
            # Re-raise extraction errors as-is
            raise
        except DatabaseError:
            # Re-raise database errors as-is
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in extraction pipeline: {e}",
                exc_info=True
            )
            raise ExtractionError(f"Extraction pipeline failed: {e}") from e
    
    async def get_record(
        self,
        table_name: str,
        record_id: Optional[UUID] = None,
        hospitalization_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        limit: int = 1
    ) -> Optional[HospitalSummary | ClinicalSummary] | list[HospitalSummary | ClinicalSummary]:
        """
        Retrieve records from database.
        
        Args:
            table_name: Database table name
            record_id: Optional UUID to get specific record
            hospitalization_id: Optional hospitalization_id to search by
            patient_id: Optional patient_id to search by
            limit: Maximum number of records to return (for patient_id search)
            
        Returns:
            Single record, list of records, or None
            
        Raises:
            ValueError: If no search criteria provided or table not found
        """
        if not any([record_id, hospitalization_id, patient_id]):
            raise ValueError(
                "Must provide at least one of: record_id, hospitalization_id, patient_id"
            )
        
        async with self.db_session.get_session() as session:
            if table_name == "hospital_summaries":
                repo = HospitalSummaryRepository(session)
            elif table_name == "clinical_summaries":
                repo = ClinicalSummaryRepository(session)
            else:
                raise ValueError(f"No repository configured for table: {table_name}")
            
            # Get by ID
            if record_id:
                logger.info(f"Retrieving record by ID: {record_id}")
                return await repo.get_by_id(record_id)
            
            # Get by hospitalization_id
            if hospitalization_id:
                logger.info(
                    f"Retrieving record by hospitalization_id: {hospitalization_id}"
                )
                return await repo.get_by_hospitalization_id(hospitalization_id)
            
            # Get by patient_id (returns list)
            if patient_id:
                logger.info(
                    f"Retrieving records by patient_id: {patient_id} (limit={limit})"
                )
                records = await repo.get_by_patient_id(patient_id, limit=limit)
                # Return single record if limit=1 and found
                if limit == 1 and records:
                    return records[0]
                return records
    
    def list_extractors(self) -> Dict[str, Dict[str, str]]:
        """
        List all registered extractors.
        
        Returns:
            Dictionary with extractor info
        """
        extractors = {}
        for name, extractor in self.registry.list_all().items():
            extractors[name] = {
                "name": extractor.name,
                "version": extractor.version,
                "table_name": extractor.table_name,
            }
        return extractors

