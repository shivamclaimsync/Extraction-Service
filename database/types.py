"""Custom SQLAlchemy types for Pydantic model serialization."""

import json
from typing import Any, Optional

from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator


class PydanticJSONB(TypeDecorator):
    """
    SQLAlchemy type that automatically converts between Pydantic models and JSONB.
    
    This allows using the same Pydantic models for both LLM extraction output
    and database storage without duplication.
    
    Usage:
        class MyTable(Base):
            data = Column(PydanticJSONB(MyPydanticModel))
    """
    
    impl = JSONB
    cache_ok = True
    
    def __init__(self, pydantic_model: type[BaseModel], *args, **kwargs):
        """
        Initialize with a Pydantic model class.
        
        Args:
            pydantic_model: The Pydantic model class to use for serialization
        """
        super().__init__(*args, **kwargs)
        self.pydantic_model = pydantic_model
    
    def process_bind_param(self, value: Any, dialect) -> Optional[dict]:
        """
        Convert Pydantic model to dict for database storage.
        
        Args:
            value: Pydantic model instance or dict
            dialect: SQLAlchemy dialect
            
        Returns:
            Dictionary representation for JSONB storage
        """
        if value is None:
            return None
        
        # If it's already a Pydantic model, convert to dict
        if isinstance(value, BaseModel):
            return value.model_dump()
        
        # If it's a dict, return as is
        if isinstance(value, dict):
            return value
        
        raise ValueError(
            f"Expected {self.pydantic_model.__name__} or dict, got {type(value)}"
        )
    
    def process_result_value(self, value: Any, dialect) -> Optional[BaseModel]:
        """
        Convert dict from database to Pydantic model.
        
        Args:
            value: Dictionary from JSONB column
            dialect: SQLAlchemy dialect
            
        Returns:
            Pydantic model instance
        """
        if value is None:
            return None
        
        # Parse JSON string if needed (shouldn't happen with JSONB but be safe)
        if isinstance(value, str):
            value = json.loads(value)
        
        # Convert dict to Pydantic model
        return self.pydantic_model(**value)

