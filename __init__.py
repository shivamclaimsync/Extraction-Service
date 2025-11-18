"""Extraction service package."""

# Import extractors to trigger auto-registration
from .extractors import HospitalSummaryExtractor, ClinicalSummaryExtractor

# Import core components
from .core import BaseExtractor, registry, ExtractionError
from .services import ExtractionService
from .database import DatabaseSession, init_db, get_db, Base

__all__ = [
    # Extractors
    "HospitalSummaryExtractor",
    "ClinicalSummaryExtractor",
    # Core
    "BaseExtractor",
    "registry",
    "ExtractionError",
    # Services
    "ExtractionService",
    # Database
    "DatabaseSession",
    "init_db",
    "get_db",
    "Base",
]

