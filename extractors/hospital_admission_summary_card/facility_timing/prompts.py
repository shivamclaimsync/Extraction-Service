"""Prompts for facility and timing data extraction."""

system_prompt = """
You are a medical AI assistant extracting facility and timing information from clinical documents.

Extract administrative data exactly as documented.
Use null for missing optional fields. Respond only in valid JSON format.
"""

facility_timing_prompt = '''
Extract facility and timing information from the clinical document and return as JSON.

**Core Principle**: Extract only explicitly documented information. Do NOT infer, assume, or invent data.

---

## Output Schema

```json
{{
  "facility": {{
    "facility_name": "string (required)",
    "facility_type": "acute_care|psychiatric|rehabilitation|ltac (default: acute_care)",
    "facility_id": "string|null",
    "address": {{
      "street": "string|null",
      "city": "string|null", 
      "state": "string|null",
      "zip": "string|null"
    }} // omit address object entirely if no address data found
  }},
  "timing": {{
    "admission_date": "Date string (required)",
    "admission_time": "HH:MM|null",
    "discharge_date": " Date string (required)", 
    "discharge_time": " Time string (HH:MM)|null",
    "admission_source": "emergency_dept|direct_admission|transfer|scheduled|null",
    "discharge_disposition": "home|snf|home_health|rehab|transfer|expired|null"
  }},
  "patient_id": "string|null",
  "hospitalization_id": "string|null"
}}
```

---

## Extraction Instructions

### Facility Information

**facility_name** (required):
- Look in: Document header, letterhead, footer, contact information
- Extract exact name as written (e.g., "Memorial Hospital", "St. Mary's Medical Center")
- If not found: Use "Unknown Facility"

**facility_type** (default: "acute_care"):
- acute_care: General hospitals, ED, urgent care
- psychiatric: Mental health facilities
- rehabilitation: Rehab centers, inpatient rehab
- ltac: Long-term acute care
- If unclear: Use "acute_care"

**facility_id**:
- Look for: Facility codes, NPI, location IDs
- Only extract if explicitly labeled as facility identifier
- If not found: null

**address**:
- Extract any available: street, city, state, zip
- If NO address information present: Omit the entire address object
- If partial address present: Include object with available fields

---




**admission_date** (required):
- Look for (in order):
  1. "Admission Date:", "Date of Admission:"
  2. "Encounter Date:", "Service Date:", "Visit Date:"
  3. Document/note creation date in header
  4. ED arrival/triage timestamp
  5. Date in "History of Present Illness" mentioning when patient arrived
- Include time in ISO format if available

**admission_time**:
- Separate field for time in HH:MM format (24-hour)
- Extract if explicitly mentioned (e.g., "admitted at 14:30", timestamp shows specific time)
- If not available: null

**discharge_date** (required):
- Look for (in order):
  1. "Discharge Date:", "Date of Discharge:"
  2. "End Date:", "Service End Date:"
  3. For ED/outpatient: Look for note completion, verification, or sign-off timestamp
  4. "Patient discharged on [date]" in Medical Decision Making
  5. For same-day visits: May be same as admission date
- Include time in ISO format if available

**discharge_time**:
- Separate field for time in HH:MM format (24-hour)
- Extract if explicitly mentioned
- For ED reports: Check verification timestamp, sign-off time, or "patient discharged at" statements
- If not available: null

**admission_source**:
- emergency_dept: "via ED", "emergency department", "brought by EMS", "presenting to ER"
- direct_admission: "directly admitted", "direct admission"
- transfer: "transferred from [facility]", "transfer from"
- scheduled: "scheduled admission", "elective admission", "planned"
- If unclear or not mentioned: null

**discharge_disposition**:
- home: "discharged home", "sent home", "to home"
- snf: "skilled nursing facility", "SNF", "nursing home"
- home_health: "home with services", "home health", "VNA"
- rehab: "rehabilitation facility", "inpatient rehab"
- transfer: "transferred to [facility]"
- expired: "expired", "deceased", "passed away"
- If unclear or not mentioned: null

---

### Patient & Encounter Identifiers

**patient_id**:
- Look for: "Patient ID:", "MRN:", "Medical Record Number:", "Patient Number:"
- Extract exact value as documented (e.g., "10838402", "MRN-12345")
- If not found: null

**hospitalization_id**:
- Look for: "DOC_ID:", "Account Number:", "Encounter ID:", "Visit ID:", "Admission Number:"
- Extract exact value (including UUIDs, alphanumeric codes)
- If not found: null

---

## Validation Checklist

Before returning JSON, verify:

- [ ] facility_name is not empty
- [ ] All dates are in `YYYY-MM-DD`
- [ ] discharge_date >= admission_date (chronologically valid)
- [ ] Times are in HH:MM format (00:00 to 23:59)
- [ ] Facility type is one of: acute_care, psychiatric, rehabilitation, ltac
- [ ] Admission source (if present) is valid enum value
- [ ] Discharge disposition (if present) is valid enum value
- [ ] No fabricated data - only extract what's explicitly documented

---

## Example Outputs

**Example 1 - Complete ED Visit**:
```json
{{
  "facility": {{
    "facility_name": "University Medical Center",
    "facility_type": "acute_care",
    "address": {{
      "street": "2325 N Main Rd",
      "city": "Springfield",
      "state": "IL",
      "zip": "49686"
    }}
  }},
  "timing": {{
    "admission_date": "2025-10-12",
    "admission_time": "03:59",
    "discharge_date": "2025-10-12",
    "discharge_time": "06:46",
    "admission_source": "emergency_dept",
    "discharge_disposition": "home"
  }},
  "patient_id": "10838402",
  "hospitalization_id": "4002562000-01-1508"
}}
```

**Example 2 - Inpatient Admission (No Times)**:
```json
{{
  "facility": {{
    "facility_name": "Memorial Hospital",
    "facility_type": "acute_care"
  }},
  "timing": {{
    "admission_date": "2025-06-10",
    "admission_time": null,
    "discharge_date": "2025-06-15",
    "discharge_time": null,
    "admission_source": "direct_admission",
    "discharge_disposition": "snf"
  }},
  "patient_id": "98765",
  "hospitalization_id": null
}}
```
---

<clinical_note>
{clinical_text}
</clinical_note>

Extract the facility and timing data from above. Return ONLY the JSON object, no additional text.
'''

__all__ = ["system_prompt", "facility_timing_prompt"]

