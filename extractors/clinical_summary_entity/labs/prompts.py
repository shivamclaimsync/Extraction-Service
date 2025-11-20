"""Prompts for laboratory result extraction."""

system_prompt = """You are a medical data extraction specialist. Extract laboratory test results from clinical documents.

Labs = blood tests, urine tests, cultures. NOT vitals or imaging. Return valid JSON only."""

labs_prompt = """Extract laboratory results from this clinical note.

<clinical_note>
{clinical_text}
</clinical_note>

---

## YOUR TASK

Extract lab results in 3 steps:
1. Find patient IDs
2. Find laboratory tests (blood/urine tests only)
3. Format as JSON

---

## STEP 1: FIND IDs

**patient_id:**
- Look for "MRN:" in document header
- Extract the number after it (8-10 digits)
- Example: "MRN: 10838402" → "10838402"

**hospitalization_id:**
- Look for "Account Number:" in document header
- Extract the number after it (~10 digits)
- Example: "Account Number: 4002138129" → "4002138129"

---

## STEP 2: FIND LABORATORY TESTS

**What ARE laboratory tests:**
✅ Blood tests: CBC, hemoglobin, WBC, platelets, neutrophils
✅ Chemistry: BMP, CMP, sodium, potassium, chloride, CO2, glucose, creatinine, BUN
✅ Cardiac markers: Troponin, BNP, CK-MB
✅ Liver function: ALT, AST, bilirubin, alkaline phosphatase, albumin
✅ Coagulation: PT, PTT, INR
✅ Arterial blood gas: pH, pO2, pCO2, lactate, base excess
✅ Urine tests: Urinalysis, urine culture
✅ Cultures: Blood culture, sputum culture
✅ Other: HbA1c, TSH, drug levels

**What are NOT laboratory tests (DO NOT extract):**
❌ Vital signs: Temperature, heart rate, respiratory rate, blood pressure, SpO2
❌ Imaging: X-ray, CT, MRI, ultrasound, ECHO
❌ Physical measurements: Height, weight, BMI
❌ ECG/EKG results

**Where to look:**
- Laboratory Results section
- Lab Values section
- Diagnostic Results section (but skip imaging)
- Text mentioning specific lab values (e.g., "creatinine 2.4")

**If NO lab tests found:**
- Return empty array: "lab_results": []
- This is common for ED visits where no labs were drawn

---

## STEP 3: EXTRACT EACH LAB TEST

For each lab test found, extract:

**test_name:** 
- Full name (e.g., "Creatinine", "White Blood Cell Count", "Troponin I")

**test_category:**
- "hematology": CBC components, WBC, RBC, hemoglobin, hematocrit, platelets
- "chemistry": BMP, CMP, electrolytes, glucose, creatinine, BUN
- "cardiac": Troponin, BNP, CK-MB
- "hepatic": ALT, AST, bilirubin, alkaline phosphatase, albumin
- "coagulation": PT, PTT, INR
- "arterial_blood_gas": pH, pO2, pCO2, lactate, base excess
- "urinalysis": Urine tests
- "endocrine": TSH, cortisol, HbA1c
- "other": Doesn't fit above

**value:**
- The numeric or text result
- Examples: 2.4, "Positive", "Negative", ">1000"

**unit:**
- Unit of measurement
- Examples: "mg/dL", "mmol/L", "g/dL", "%", "cells/μL"

**status:**
- "critical": Life-threatening value
- "abnormal_high": Above normal range
- "abnormal_low": Below normal range
- "normal": Within normal range

**reference_range:**
- Text description if provided
- Example: "0.6-1.2 mg/dL", "3.5-5.0 mEq/L"

**collected_at:**
- Date/time when lab was collected
- Format: "YYYY-MM-DD HH:MM" or "YYYY-MM-DD"
- Set to null if not documented

**clinical_significance:**
- Brief note on why this lab matters (if document explains)
- Example: "Elevated indicating acute kidney injury"
- Null if not explained

**documented_in_section:**
- Where you found this lab
- Example: "Laboratory Results", "Diagnostic Results"

---

## STEP 4: CREATE SUMMARY

Count your extracted labs:
```json
"lab_summary": {{
  "total_tests": <count all labs>,
  "critical_count": <count status="critical">,
  "abnormal_count": <count status="abnormal_high" or "abnormal_low">,
  "normal_count": <count status="normal">
}}
```

---

## OUTPUT JSON SCHEMA
```json
{{
  "lab_results": [
    {{
      "id": "lab_001",
      "test_name": "string",
      "test_category": "hematology|chemistry|cardiac|hepatic|coagulation|arterial_blood_gas|urinalysis|endocrine|other",
      "value": "number or string",
      "unit": "string or null",
      "status": "critical|abnormal_high|abnormal_low|normal",
      "reference_range": "string or null",
      "reference_range_min": "number or null",
      "reference_range_max": "number or null",
      "baseline_value": "number or string or null",
      "collected_at": "YYYY-MM-DD HH:MM or null",
      "clinical_significance": "string or null",
      "documented_in_section": "string"
    }}
  ],
  "lab_summary": {{
    "total_tests": 0,
    "critical_count": 0,
    "abnormal_count": 0,
    "normal_count": 0
  }},
  "patient_id": "MRN string",
  "hospitalization_id": "Account Number string"
}}
```

---

## EXAMPLES

### Example 1: No Labs Drawn

**Clinical note snippet:**
```
MRN: 10838402
Account Number: 4002138129
Emergency Department Visit
Vitals: T 36.8°C, HR 93, BP 136/41, SpO2 100%
Chest X-ray: No acute process
Patient discharged home
```

**Output:**
```json
{{
  "lab_results": [],
  "lab_summary": {{
    "total_tests": 0,
    "critical_count": 0,
    "abnormal_count": 0,
    "normal_count": 0
  }},
  "patient_id": "10838402",
  "hospitalization_id": "4002138129"
}}
```

### Example 2: Labs Present

**Clinical note snippet:**
```
MRN: 12345678
Account Number: 9876543210

Laboratory Results (2025-08-29 08:00):
- Creatinine: 2.4 mg/dL (elevated, baseline 1.1)
- BUN: 45 mg/dL (elevated)
- Sodium: 138 mEq/L (normal)
- Potassium: 5.2 mEq/L (elevated)
- Troponin I: 0.03 ng/mL (normal)
```

**Output:**
```json
{{
  "lab_results": [
    {{
      "id": "lab_001",
      "test_name": "Creatinine",
      "test_category": "chemistry",
      "value": 2.4,
      "unit": "mg/dL",
      "status": "abnormal_high",
      "reference_range": "0.6-1.2 mg/dL",
      "reference_range_min": 0.6,
      "reference_range_max": 1.2,
      "baseline_value": 1.1,
      "collected_at": "2025-08-29 08:00",
      "clinical_significance": "Elevated, suggesting acute kidney injury",
      "documented_in_section": "Laboratory Results"
    }},
    {{
      "id": "lab_002",
      "test_name": "Blood Urea Nitrogen",
      "test_category": "chemistry",
      "value": 45,
      "unit": "mg/dL",
      "status": "abnormal_high",
      "reference_range": "7-20 mg/dL",
      "reference_range_min": 7,
      "reference_range_max": 20,
      "baseline_value": null,
      "collected_at": "2025-08-29 08:00",
      "clinical_significance": null,
      "documented_in_section": "Laboratory Results"
    }},
    {{
      "id": "lab_003",
      "test_name": "Sodium",
      "test_category": "chemistry",
      "value": 138,
      "unit": "mEq/L",
      "status": "normal",
      "reference_range": "135-145 mEq/L",
      "reference_range_min": 135,
      "reference_range_max": 145,
      "baseline_value": null,
      "collected_at": "2025-08-29 08:00",
      "clinical_significance": null,
      "documented_in_section": "Laboratory Results"
    }},
    {{
      "id": "lab_004",
      "test_name": "Potassium",
      "test_category": "chemistry",
      "value": 5.2,
      "unit": "mEq/L",
      "status": "abnormal_high",
      "reference_range": "3.5-5.0 mEq/L",
      "reference_range_min": 3.5,
      "reference_range_max": 5.0,
      "baseline_value": null,
      "collected_at": "2025-08-29 08:00",
      "clinical_significance": null,
      "documented_in_section": "Laboratory Results"
    }},
    {{
      "id": "lab_005",
      "test_name": "Troponin I",
      "test_category": "cardiac",
      "value": 0.03,
      "unit": "ng/mL",
      "status": "normal",
      "reference_range": "<0.04 ng/mL",
      "reference_range_min": null,
      "reference_range_max": 0.04,
      "baseline_value": null,
      "collected_at": "2025-08-29 08:00",
      "clinical_significance": "Rules out acute myocardial infarction",
      "documented_in_section": "Laboratory Results"
    }}
  ],
  "lab_summary": {{
    "total_tests": 5,
    "critical_count": 0,
    "abnormal_count": 3,
    "normal_count": 2
  }},
  "patient_id": "12345678",
  "hospitalization_id": "9876543210"
}}
```

---

## KEY RULES

1. **IDs are required** - Extract patient_id and hospitalization_id from document header
2. **Labs only** - Do NOT extract vital signs, imaging, or physical measurements
3. **Empty is OK** - If no labs drawn, return empty array (common in ED visits)
4. **Categories matter** - Use correct test_category (not "metabolic" or "electrolytes" for vitals)
5. **Sequential IDs** - Use lab_001, lab_002, lab_003, etc.
6. **Status based on ranges** - Compare value to reference range to determine status
7. **Null when unknown** - Use null for fields without information (don't guess)

Return only JSON. No other text.
"""

__all__ = ["system_prompt", "labs_prompt"]

