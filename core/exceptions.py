"""Exception classes for the extraction service."""


class ExtractionError(Exception):
    """
    Base exception for extraction-related errors.
    
    Raised when extraction from clinical text fails due to:
    - LLM API errors
    - Parsing failures
    - Validation errors
    - Unexpected extraction issues
    """
    pass


class DatabaseError(Exception):
    """
    Base exception for database-related errors.
    
    Raised when database operations fail due to:
    - Connection errors
    - Query execution failures
    - Transaction errors
    - Other database-level issues
    """
    pass


class DuplicateRecordError(DatabaseError):
    """
    Exception raised when attempting to create a duplicate record.
    
    Raised when:
    - Unique constraint violations occur
    - Record with same identifier already exists
    - Duplicate data insertion attempts
    """
    pass

