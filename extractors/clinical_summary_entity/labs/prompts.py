"""Prompts for laboratory result extraction."""

system_prompt = """
You are a clinical documentation specialist. Extract significant laboratory results
from discharge summaries and respond strictly in JSON matching the provided schema.
"""

labs_prompt = """
Read the discharge summary and populate the lab results schema. Return only JSON.

Schema:
{{
  "lab_results": LabTest[],
  "lab_summary": {{
    "total_tests": number,
    "critical_count": number,
    "abnormal_count": number,
    "normal_count": number
  }}
}}

LabTest:
{{
  "id": string,
  "test_name": string,
  "test_code": string | null,
  "test_category": "chemistry" | "hematology" | "coagulation" | "arterial_blood_gas" |
                   "urinalysis" | "metabolic" | "cardiac" | "hepatic" | "renal" |
                   "electrolytes" | "endocrine" | "toxicology" | null,
  "value": number | string,
  "unit": string | null,
  "status": "critical" | "abnormal_high" | "abnormal_low" | "normal",
  "reference_range": string | null,
  "reference_range_min": number | null,
  "reference_range_max": number | null,
  "baseline_value": number | string | null,
  "change_from_baseline": {{
    "absolute": number,
    "percent": number,
    "direction": string
  }} | null,
  "collected_at": string | null,
  "resulted_at": string | null,
  "hospital_day": number | null,
  "clinical_significance": string | null,
  "action_taken": string | null,
  "critical_alert": boolean,
  "provider_notified": boolean
}}

Instructions:
1. List each lab test emphasized in the summary (critical or abnormal). Assign sequential ids (lab_001, etc.).
2. Populate reference ranges and baseline information when provided.
3. Set status according to narrative cues (e.g., "elevated" => abnormal_high, "critical value" => critical).
4. Capture follow-up actions (e.g., "IV fluids initiated") in action_taken; leave null if unstated.
5. Compute lab_summary counts based on the array contents.
6. Always include `lab_results` (use []) and `lab_summary`.

<clinical_note>
{clinical_text}
</clinical_note>
"""

__all__ = ["system_prompt", "labs_prompt"]

