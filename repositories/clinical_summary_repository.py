"""Repository for clinical_summaries table operations."""

from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from core.exceptions import DatabaseError, DuplicateRecordError
from repositories.models.clinical_summary_db import ClinicalSummary
from extractors.clinical_summary_entity.aggregator import (
    ClinicalSummaryResult,
)

logger = logging.getLogger(__name__)


class ClinicalSummaryRepository:
    """
    Repository for CRUD operations on clinical_summaries table.
    
    Stores each section of the clinical summary in separate JSONB columns.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session.
        
        Args:
            session: SQLAlchemy AsyncSession instance
        """
        self.session = session
    
    async def create(self, data: Dict[str, Any]) -> ClinicalSummary:
        """
        Create a new clinical summary record.
        
        Args:
            data: Dictionary with:
                  - patient_id: Patient identifier (required)
                  - summary: ClinicalSummaryResult Pydantic model (required)
                  
        Returns:
            Created ClinicalSummary instance with all fields populated
            
        Raises:
            DatabaseError: For database errors
        """
        try:
            # Extract the ClinicalSummaryResult from data
            summary_result: ClinicalSummaryResult = data.get("summary")
            if not summary_result:
                raise ValueError("'summary' (ClinicalSummaryResult) is required in data")
            
            # Extract patient_id
            patient_id = data.get("patient_id")
            if not patient_id:
                # Try to get from metadata
                patient_id = summary_result.metadata.patient_id
            if not patient_id:
                raise ValueError("patient_id is required")
            
            # Extract hospitalization_id from metadata
            hospitalization_id = summary_result.metadata.hospitalization_id
            
            # Break apart the summary into separate sections
            # Convert each Pydantic model to dict for JSONB storage
            db_data = {
                "patient_id": patient_id,
                "hospitalization_id": hospitalization_id,
                "patient_presentation": (
                    summary_result.summary.patient_presentation.model_dump(mode='json')
                    if summary_result.summary.patient_presentation else None
                ),
                "relevant_history": (
                    summary_result.summary.relevant_history.model_dump(mode='json')
                    if summary_result.summary.relevant_history else None
                ),
                "clinical_findings": (
                    summary_result.summary.clinical_findings.model_dump(mode='json')
                    if summary_result.summary.clinical_findings else None
                ),
                "clinical_assessment": (
                    summary_result.summary.clinical_assessment.model_dump(mode='json')
                    if summary_result.summary.clinical_assessment else None
                ),
                "hospital_course": (
                    summary_result.summary.hospital_course.model_dump(mode='json')
                    if summary_result.summary.hospital_course else None
                ),
                "follow_up_plan": (
                    summary_result.summary.follow_up_plan.model_dump(mode='json')
                    if summary_result.summary.follow_up_plan else None
                ),
                "treatments_procedures": (
                    [t.model_dump(mode='json') for t in summary_result.summary.treatments_procedures]
                    if summary_result.summary.treatments_procedures else None
                ),
                "lab_results": (
                    [lab.model_dump(mode='json') for lab in summary_result.summary.lab_results]
                    if summary_result.summary.lab_results else None
                ),
            }
            
            # Create model instance
            db_record = ClinicalSummary(**db_data)
            
            self.session.add(db_record)
            await self.session.commit()
            await self.session.refresh(db_record)
            
            logger.info(
                f"Created clinical summary: id={db_record.id}, "
                f"patient_id={db_record.patient_id}, "
                f"hospitalization_id={db_record.hospitalization_id}"
            )
            
            return db_record
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Database integrity error: {e}")
            raise DatabaseError(f"Failed to create record: {e}") from e
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create clinical summary: {e}", exc_info=True)
            raise DatabaseError(f"Failed to create record: {e}") from e
    
    async def get_by_id(self, record_id: UUID) -> Optional[ClinicalSummary]:
        """
        Get clinical summary by ID.
        
        Args:
            record_id: UUID of the record
            
        Returns:
            ClinicalSummary instance or None if not found
        """
        stmt = select(ClinicalSummary).where(ClinicalSummary.id == record_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            logger.debug(f"Found clinical summary: {record_id}")
        else:
            logger.debug(f"Clinical summary not found: {record_id}")
        
        return record
    
    async def get_by_hospitalization_id(
        self,
        hospitalization_id: str
    ) -> Optional[ClinicalSummary]:
        """
        Get clinical summary by hospitalization_id.
        
        Args:
            hospitalization_id: Hospitalization/encounter identifier
            
        Returns:
            ClinicalSummary instance or None if not found
        """
        # Now hospitalization_id is a direct column, so simple query
        stmt = select(ClinicalSummary).where(
            ClinicalSummary.hospitalization_id == hospitalization_id
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            logger.debug(f"Found clinical summary by hospitalization_id: {hospitalization_id}")
        else:
            logger.debug(f"Clinical summary not found for hospitalization_id: {hospitalization_id}")
        
        return record
    
    async def get_by_patient_id(
        self,
        patient_id: str,
        limit: int = 10
    ) -> List[ClinicalSummary]:
        """
        Get all clinical summaries for a patient.
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of records to return
            
        Returns:
            List of ClinicalSummary instances, ordered by created_at desc
        """
        stmt = (
            select(ClinicalSummary)
            .where(ClinicalSummary.patient_id == patient_id)
            .order_by(ClinicalSummary.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        records = list(result.scalars().all())
        
        logger.debug(f"Found {len(records)} clinical summaries for patient {patient_id}")
        
        return records
    
    async def update(
        self,
        record_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[ClinicalSummary]:
        """
        Update an existing clinical summary record.
        
        Args:
            record_id: UUID of the record to update
            data: Dictionary with fields to update
            
        Returns:
            Updated ClinicalSummary instance or None if not found
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            # Get existing record
            stmt = select(ClinicalSummary).where(ClinicalSummary.id == record_id)
            result = await self.session.execute(stmt)
            db_record = result.scalar_one_or_none()
            
            if not db_record:
                logger.warning(f"Clinical summary not found for update: {record_id}")
                return None
            
            # Update fields
            for key, value in data.items():
                if hasattr(db_record, key) and key != 'id':
                    setattr(db_record, key, value)
            
            await self.session.commit()
            await self.session.refresh(db_record)
            
            logger.info(f"Updated clinical summary: {record_id}")
            
            return db_record
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update clinical summary: {e}", exc_info=True)
            raise DatabaseError(f"Failed to update record: {e}") from e
    
    async def delete(self, record_id: UUID) -> bool:
        """
        Delete a clinical summary record.
        
        Args:
            record_id: UUID of the record to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseError: If delete fails
        """
        try:
            # Get existing record
            stmt = select(ClinicalSummary).where(ClinicalSummary.id == record_id)
            result = await self.session.execute(stmt)
            db_record = result.scalar_one_or_none()
            
            if not db_record:
                logger.warning(f"Clinical summary not found for deletion: {record_id}")
                return False
            
            await self.session.delete(db_record)
            await self.session.commit()
            
            logger.info(f"Deleted clinical summary: {record_id}")
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete clinical summary: {e}", exc_info=True)
            raise DatabaseError(f"Failed to delete record: {e}") from e

