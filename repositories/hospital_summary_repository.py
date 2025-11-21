"""Repository for hospital_summaries table operations."""

from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from core.exceptions import DatabaseError, DuplicateRecordError
from repositories.models.hospital_summary_db import HospitalSummary
from extractors.hospital_admission_summary_card.model import (
    HospitalAdmissionSummaryCard,
)

logger = logging.getLogger(__name__)


class HospitalSummaryRepository:
    """
    Repository for CRUD operations on hospital_summaries table.
    
    Stores each section of the hospital admission summary in separate JSONB columns.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session.
        
        Args:
            session: SQLAlchemy AsyncSession instance
        """
        self.session = session
    
    async def create(self, data: Dict[str, Any]) -> HospitalSummary:
        """
        Create a new hospital summary record.
        
        Args:
            data: Dictionary with:
                  - patient_id: Patient identifier (required)
                  - summary_card: HospitalAdmissionSummaryCard Pydantic model (required)
                  OR legacy format with separate fields (facility, timing, etc.)
                  
        Returns:
            Created HospitalSummary instance with all fields populated
            
        Raises:
            DuplicateRecordError: If hospitalization_id already exists
            DatabaseError: For other database errors
        """
        try:
            # Extract the HospitalAdmissionSummaryCard from data
            summary_card: HospitalAdmissionSummaryCard = data.get("summary_card")
            
            # Handle legacy format: construct summary_card from separate fields
            if not summary_card:
                summary_card = HospitalAdmissionSummaryCard(
                    facility=data["facility"],
                    timing=data["timing"],
                    diagnosis=data["diagnosis"],
                    medication_risk_assessment=data["medication_risk_assessment"],
                    hospitalization_id=data.get("hospitalization_id"),
                )
            
            # Extract patient_id
            patient_id = data.get("patient_id")
            if not patient_id:
                raise ValueError("patient_id is required")
            
            # Extract hospitalization_id from summary_card
            hospitalization_id = summary_card.hospitalization_id
            
            # Calculate length_of_stay_days from timing
            length_of_stay_days = summary_card.length_of_stay_days
            
            # Break apart the summary_card into separate sections
            # Convert each Pydantic model to dict for JSONB storage
            db_data = {
                "patient_id": patient_id,
                "hospitalization_id": hospitalization_id,
                "facility": summary_card.facility.model_dump(mode='json'),
                "timing": summary_card.timing.model_dump(mode='json'),
                "diagnosis": summary_card.diagnosis.model_dump(mode='json'),
                "medication_risk_assessment": summary_card.medication_risk_assessment.model_dump(mode='json'),
                "length_of_stay_days": length_of_stay_days,
            }
            
            # Create model instance
            db_record = HospitalSummary(**db_data)
            
            self.session.add(db_record)
            await self.session.commit()
            await self.session.refresh(db_record)
            
            logger.info(
                f"Created hospital summary: id={db_record.id}, "
                f"hospitalization_id={db_record.hospitalization_id}"
            )
            
            return db_record
            
        except IntegrityError as e:
            await self.session.rollback()
            
            # Check if it's a duplicate hospitalization_id
            # Extract hospitalization_id from the data we tried to save
            hospitalization_id = None
            if 'summary_card' in locals() and summary_card:
                hospitalization_id = summary_card.hospitalization_id
            elif 'db_data' in locals():
                hospitalization_id = db_data.get("hospitalization_id")
            else:
                hospitalization_id = data.get("hospitalization_id")
            
            if hospitalization_id and "hospitalization_id" in str(e.orig):
                logger.error(
                    f"Duplicate hospitalization_id: {hospitalization_id}"
                )
                raise DuplicateRecordError(
                    "Record with this hospitalization_id already exists",
                    field="hospitalization_id",
                    value=hospitalization_id
                ) from e
            
            logger.error(f"Database integrity error: {e}")
            raise DatabaseError(f"Failed to create record: {e}") from e
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create hospital summary: {e}", exc_info=True)
            raise DatabaseError(f"Failed to create record: {e}") from e
    
    async def get_by_id(self, record_id: UUID) -> Optional[HospitalSummary]:
        """
        Get hospital summary by ID.
        
        Args:
            record_id: UUID of the record
            
        Returns:
            HospitalSummary instance or None if not found
        """
        stmt = select(HospitalSummary).where(HospitalSummary.id == record_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            logger.debug(f"Found hospital summary: {record_id}")
        else:
            logger.debug(f"Hospital summary not found: {record_id}")
        
        return record
    
    async def get_by_hospitalization_id(
        self,
        hospitalization_id: str
    ) -> Optional[HospitalSummary]:
        """
        Get hospital summary by hospitalization_id.
        
        Args:
            hospitalization_id: Hospitalization/encounter identifier
            
        Returns:
            HospitalSummary instance or None if not found
        """
        # Now hospitalization_id is a direct column, so simple query
        stmt = select(HospitalSummary).where(
            HospitalSummary.hospitalization_id == hospitalization_id
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            logger.debug(f"Found hospital summary by hospitalization_id: {hospitalization_id}")
        else:
            logger.debug(f"Hospital summary not found for hospitalization_id: {hospitalization_id}")
        
        return record
    
    async def get_by_patient_id(
        self,
        patient_id: str,
        limit: int = 10
    ) -> List[HospitalSummary]:
        """
        Get all hospital summaries for a patient.
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of records to return
            
        Returns:
            List of HospitalSummary instances, ordered by created_at desc
        """
        stmt = (
            select(HospitalSummary)
            .where(HospitalSummary.patient_id == patient_id)
            .order_by(HospitalSummary.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        records = list(result.scalars().all())
        
        logger.debug(f"Found {len(records)} hospital summaries for patient {patient_id}")
        
        return records
    
    async def update(
        self,
        record_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[HospitalSummary]:
        """
        Update an existing hospital summary record.
        
        Args:
            record_id: UUID of the record to update
            data: Dictionary with fields to update
            
        Returns:
            Updated HospitalSummary instance or None if not found
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            # Get existing record
            stmt = select(HospitalSummary).where(HospitalSummary.id == record_id)
            result = await self.session.execute(stmt)
            db_record = result.scalar_one_or_none()
            
            if not db_record:
                logger.warning(f"Hospital summary not found for update: {record_id}")
                return None
            
            # Update fields
            for key, value in data.items():
                if hasattr(db_record, key) and key != 'id':
                    setattr(db_record, key, value)
            
            await self.session.commit()
            await self.session.refresh(db_record)
            
            logger.info(f"Updated hospital summary: {record_id}")
            
            return db_record
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update hospital summary: {e}", exc_info=True)
            raise DatabaseError(f"Failed to update record: {e}") from e
    
    async def delete(self, record_id: UUID) -> bool:
        """
        Delete a hospital summary record.
        
        Args:
            record_id: UUID of the record to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseError: If delete fails
        """
        try:
            # Get existing record
            stmt = select(HospitalSummary).where(HospitalSummary.id == record_id)
            result = await self.session.execute(stmt)
            db_record = result.scalar_one_or_none()
            
            if not db_record:
                logger.warning(f"Hospital summary not found for deletion: {record_id}")
                return False
            
            await self.session.delete(db_record)
            await self.session.commit()
            
            logger.info(f"Deleted hospital summary: {record_id}")
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete hospital summary: {e}", exc_info=True)
            raise DatabaseError(f"Failed to delete record: {e}") from e

