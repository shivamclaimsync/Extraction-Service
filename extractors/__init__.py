"""Extractors package - wrappers for existing extraction tools."""

from .hospital_summary_extractor import HospitalSummaryExtractor
from .clinical_summary_extractor import ClinicalSummaryExtractor

__all__ = [
    "HospitalSummaryExtractor",
    "ClinicalSummaryExtractor",
]

