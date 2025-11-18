"""Aggregator that orchestrates all hospital admission summary card extraction tools."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .diagnosis.tool import DiagnosisPydanticAITool
from .facility_timing.tool import FacilityTimingPydanticAITool
from .medication_risk.tool import MedicationRiskPydanticAITool
from .model import HospitalAdmissionSummaryCard

logger = logging.getLogger(__name__)


@dataclass
class HospitalAdmissionSummaryCardExtractor:
    """
    Orchestrator that runs all sub-extractors in parallel and combines results.

    """

    facility_timing_tool: FacilityTimingPydanticAITool = field(
        default_factory=FacilityTimingPydanticAITool
    )
    diagnosis_tool: DiagnosisPydanticAITool = field(
        default_factory=DiagnosisPydanticAITool
    )
    medication_risk_tool: MedicationRiskPydanticAITool = field(
        default_factory=MedicationRiskPydanticAITool
    )

    async def extract(
        self,
        clinical_text: str,
    ) -> HospitalAdmissionSummaryCard:
        """
        Extract all components of the hospital admission summary card.
        
        Args:
            clinical_text: The clinical document text to extract from
            
        Returns:
            HospitalAdmissionSummaryCard with all extracted data
        """
        logger.info("Starting hospital admission summary card extraction")

        # Run facility_timing FIRST to extract hospitalization_id
        facility_timing_resp = await self.facility_timing_tool.run(clinical_text)
        
        # Extract global ID
        hospitalization_id = facility_timing_resp.hospitalization_id
        
        logger.info(
            "Extracted metadata - Hospitalization ID: %s",
            hospitalization_id
        )

        # Run other extractors in parallel
        tasks = [
            self.diagnosis_tool.run(clinical_text),
            self.medication_risk_tool.run(clinical_text),
        ]

        try:
            (
                diagnosis_resp,
                medication_risk_resp,
            ) = await asyncio.gather(*tasks)

            # Ensure assessed_at timestamp is set if not provided by LLM
            if not medication_risk_resp.medication_risk_assessment.assessed_at:
                medication_risk_resp.medication_risk_assessment.assessed_at = (
                    datetime.now(timezone.utc).isoformat()
                )

            # Combine all extracted data into the summary card
            summary_card = HospitalAdmissionSummaryCard(
                facility=facility_timing_resp.facility,
                timing=facility_timing_resp.timing,
                diagnosis=diagnosis_resp.diagnosis,
                medication_risk_assessment=medication_risk_resp.medication_risk_assessment,
                hospitalization_id=hospitalization_id,
            )

            logger.info(
                "Hospital admission summary card extraction completed successfully. "
                "Length of stay: %d days, Risk level: %s",
                summary_card.length_of_stay_days,
                summary_card.medication_risk_assessment.risk_level,
            )

            return summary_card

        except Exception as exc:
            logger.error("Hospital admission summary card extraction failed: %s", exc)
            raise


__all__ = ["HospitalAdmissionSummaryCardExtractor"]

