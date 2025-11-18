"""Custom exceptions for the extraction service."""


class ExtractionError(Exception):
    """Base exception for extraction-related errors."""
    pass


class LLMExtractionError(ExtractionError):
    """Exception raised when LLM extraction fails."""
    
    def __init__(
        self,
        message: str,
        extractor_name: str = None,
        llm_response: str = None
    ):
        """
        Initialize LLM extraction error.
        
        Args:
            message: Error message
            extractor_name: Name of the extractor that failed
            llm_response: Raw LLM response if available
        """
        self.extractor_name = extractor_name
        self.llm_response = llm_response
        
        if extractor_name:
            message = f"[{extractor_name}] {message}"
        
        super().__init__(message)


class ValidationError(ExtractionError):
    """Exception raised when extracted data fails validation."""
    
    def __init__(self, message: str, field: str = None, value=None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Name of the field that failed validation
            value: Value that failed validation
        """
        self.field = field
        self.value = value
        
        if field:
            message = f"Validation failed for field '{field}': {message}"
        
        super().__init__(message)


class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass


class DuplicateRecordError(DatabaseError):
    """Exception raised when attempting to create a duplicate record."""
    
    def __init__(self, message: str, field: str = None, value=None):
        """
        Initialize duplicate record error.
        
        Args:
            message: Error message
            field: Field that caused the duplicate (e.g., 'hospitalization_id')
            value: Duplicate value
        """
        self.field = field
        self.value = value
        
        if field and value:
            message = f"{message} (field: {field}, value: {value})"
        
        super().__init__(message)

