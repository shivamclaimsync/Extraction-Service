"""Abstract base class for all extractors."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """
    Abstract base class for all extraction tools.
    
    Each extractor corresponds to one database table and orchestrates
    one or more LLM tools to extract structured data from clinical text.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """
        Initialize base extractor.
        
        Args:
            name: Unique identifier for this extractor (e.g., 'hospital_summary')
            version: Version string for tracking extractor changes
        """
        self._name = name
        self._version = version
        logger.info(f"Initialized extractor: {name} v{version}")
    
    @property
    def name(self) -> str:
        """Get extractor name."""
        return self._name
    
    @property
    def version(self) -> str:
        """Get extractor version."""
        return self._version
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """
        Get the database table name this extractor populates.
        
        Returns:
            Table name (e.g., 'hospital_summaries')
        """
        pass
    
    @abstractmethod
    async def extract(
        self,
        patient_id: str,
        raw_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from raw clinical text.
        
        This method should call the underlying LLM tools and return
        a dictionary matching the database table structure.
        
        Args:
            patient_id: Patient identifier
            raw_text: Raw clinical text to extract from
            metadata: Optional metadata dictionary
            
        Returns:
            Dictionary with keys matching database table columns.
            Pydantic models should be included directly (they will be
            automatically serialized by PydanticJSONB).
            
        Raises:
            ExtractionError: If extraction fails
            ValidationError: If extracted data fails validation
        """
        pass
    
    def validate_input(
        self,
        patient_id: str,
        raw_text: str
    ) -> None:
        """
        Validate input before extraction.
        
        Override this method for custom validation logic.
        
        Args:
            patient_id: Patient identifier
            raw_text: Raw clinical text
            
        Raises:
            ValidationError: If validation fails
        """
        if not patient_id or not patient_id.strip():
            from .exceptions import ValidationError
            raise ValidationError("patient_id is required and cannot be empty")
        
        if not raw_text or not raw_text.strip():
            from .exceptions import ValidationError
            raise ValidationError("raw_text is required and cannot be empty")
    
    def __repr__(self) -> str:
        """String representation of the extractor."""
        return f"<{self.__class__.__name__}(name={self.name}, version={self.version})>"

