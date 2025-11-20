"""Prompts for hospital course extraction."""

system_prompt = """You are a medical AI assistant extracting hospital course information from clinical documents.

Extract patient progression, outcomes, and disposition. Focus on status changes, not interventions.

Never infer. Return valid JSON only."""

course_prompt = '''Extract hospital course from this clinical note. Return ONLY valid JSON.

**Core Principle**: Extract only explicitly documented information. Focus on patient status changes and progression, not individual interventions.

<clinical_note>
{clinical_text}
</clinical_note>

---

## Output Schema

```json
{{
  "hospital_course": {{
    "timeline": [
      {{
        "event": "string",
        "time": "string or null",
        "details": "string or null"
      }}
    ],
    "narrative_summary": "string or null",
    "disposition": "discharged_home|discharged_home_with_services|admitted_observation|admitted_inpatient|transferred|left_AMA|deceased",
    "length_of_stay": "string or null",
    "patient_response": "string or null",
    "admission_date": "YYYY-MM-DD or null",
    "discharge_date": "YYYY-MM-DD or null",
    "follow_up_plans": ["array of strings or empty"]
  }},
  "patient_id": "MRN from document",
  "hospitalization_id": "account/encounter number"
}}
```

---

## Extraction Rules

### 1. Patient/Hospitalization IDs (REQUIRED)

**Extract**:
- `patient_id`: MRN (Medical Record Number)
  - Look for: "MRN:", "Medical Record Number:", patient demographics header
  - Format: Usually 8-10 digit number
  - **DO NOT use**: Document IDs, RRD numbers, request IDs

- `hospitalization_id`: Account Number or Encounter Number
  - Look for: "Account Number:", "Encounter:", "Visit Number:"
  - Format: Usually 10-digit number

**Example locations in document**:
```
MRN: 10838402
Account Number: 4002138129
```

**CRITICAL**: These are different numbers. Extract both correctly.

---

### 2. Timeline Events

**Focus on PATIENT STATUS and PROGRESSION, not interventions**

#### Include (Patient-Centered):
- ✅ Arrival/presentation: "Arrived by EMS after chemical exposure"
- ✅ Status changes: "Respiratory status improved", "Symptoms resolved"
- ✅ Clinical findings: "Physical exam showed mild wheezing"
- ✅ Diagnostic results: "Chest X-ray negative for acute process"
- ✅ Patient response: "Breathing better after treatment"
- ✅ Milestones: "Cleared for discharge", "Admitted to ICU"
- ✅ Prior same-day visits: "Seen earlier today for COPD exacerbation"

#### Exclude (Treatment-Focused):
- ❌ Individual medications: "Started on antibiotics"
- ❌ Procedures: "IV placed"
- ❌ Labs ordered: "CBC drawn"

#### The Gray Area - Include Patient Response:
- ✅ "Improved after DuoNeb treatment" (patient response)
- ❌ "DuoNeb administered" (treatment action)

**Event Structure**:
- `event`: What happened to the patient (status change, milestone, outcome)
- `time`: When it happened
  - Use actual timestamps if available: "2025-08-29 21:30 EDT"
  - Use relative: "On arrival", "During ED stay", "Hospital Day 2"
  - Use "After approximately X hours" for duration-based
- `details`: Additional context (vital signs, specific findings, patient feelings)

**Timeline Completeness**:
- Include 5-10 events covering full encounter
- Include prior same-day visits if mentioned
- Include key diagnostic findings
- Include treatment response/outcomes
- Include discharge planning

---

### 3. Narrative Summary

**Format**: 2-4 connected sentences (prose, not bullets)

**Include**:
1. Patient demographics and presentation reason
2. Key clinical findings or events
3. Treatment response/outcome
4. Disposition

**Example**:
"85-year-old female with COPD presented to ED after chemical fume exposure from burning plastic on stove. Earlier the same day, she was seen for COPD exacerbation and started on Decadron. Physical exam showed mild wheezing, chest X-ray was negative, and she improved with bronchodilator therapy. Discharged home stable after 1.5 hours with follow-up instructions."

**Set to null** if insufficient information to create coherent summary.

---

### 4. Disposition

**Standard values** (choose ONE):
- `discharged_home`: Patient went home
- `discharged_home_with_services`: Home with home health, PT, nursing, etc.
- `admitted_observation`: Admitted for observation
- `admitted_inpatient`: Full inpatient admission
- `transferred`: Transferred to another facility
- `left_AMA`: Left against medical advice
- `deceased`: Patient died

**Determination**:
- Look in: Disposition section, Assessment/Plan, Discharge instructions
- For ED visits: Usually "discharged_home" unless services mentioned
- If services mentioned: "discharged_home_with_services"

**Set to null** only if truly not documented.

---

### 5. Length of Stay

**Extract as documented**:
- "Same day", "Same day ED visit"
- "Approximately X hours" (e.g., "Approximately 1.5 hours")
- "X days" for inpatient
- "4 hour ED stay"

**Calculate if dates available**:
- If admission: 2025-08-29, discharge: 2025-08-29 → "Same day"
- If admission: 2025-08-29, discharge: 2025-08-31 → "2 days"

**Look in**:
- History of Present Illness: "Patient here for approximate hour and a half"
- Medical Decision Making
- Discharge instructions

**Set to null** if not documented or calculable.

---

### 6. Patient Response

**Definition**: Overall response to treatment and clinical course

**Extract statements about**:
- Improvement: "Breathing better", "Symptoms improved"
- Resolution: "Symptoms resolved"
- Stability: "Patient at baseline", "Condition stabilized"
- Worsening: "Deteriorated despite treatment"

**Format**: 1-2 sentences summarizing overall response

**Example**:
"Patient's respiratory status improved after nebulizer therapy. By discharge, she was breathing better and symptoms had resolved."

**Look in**:
- Assessment/Plan
- Medical Decision Making
- Discharge summary

**Set to null** if response not explicitly documented.

---

### 7. Admission/Discharge Dates

**Format**: YYYY-MM-DD

**Extract from**:
- Document header
- "Admission Date:", "Discharge Date:"
- Visit dates in header section

**For ED visits**: Often same date for both

**Example**:
```json
"admission_date": "2025-08-29",
"discharge_date": "2025-08-29"
```

**Set to null** if dates not clearly documented.

---

### 8. Follow-Up Plans

**Extract documented follow-up instructions**:
- PCP appointments: "Follow up with Dr. Smith within 24-48 hours"
- Specialist follow-up: "Cardiology follow-up in 1 week"
- Return precautions: "Return to ER if symptoms worsen"
- Medication instructions: "Continue home medications as prescribed"
- Test follow-up: "Repeat labs in 1 week"

**Format**: Array of strings, each a complete instruction

**Look in**:
- Follow-Up section
- Discharge Instructions
- Assessment/Plan

**Use empty array []** if no follow-up documented.

---

## Examples

### Example 1: ED Chemical Exposure
```json
{{
  "hospital_course": {{
    "timeline": [
      {{
        "event": "Seen earlier same day in ER for chest pain and COPD exacerbation",
        "time": "Earlier on 2025-08-29",
        "details": "Diagnosed with COPD exacerbation, started on Decadron"
      }},
      {{
        "event": "Arrived by EMS after chemical fume exposure",
        "time": "2025-08-29 21:30 EDT",
        "details": "Plastic spice rack melted on stove, patient exposed to burning plastic fumes, reports smoke inhalation and shortness of breath"
      }},
      {{
        "event": "Initial assessment completed",
        "time": "On arrival",
        "details": "Vitals stable: T 36.8°C, HR 93, BP 136/41, SpO2 100%. Physical exam showed mild bilateral wheezing, no facial burns or soot in oropharynx"
      }},
      {{
        "event": "Chest X-ray performed",
        "time": "2025-08-29 22:08 EDT",
        "details": "Result: No acute cardiopulmonary process"
      }},
      {{
        "event": "Respiratory status improved with treatment",
        "time": "After approximately 1.5 hours",
        "details": "Patient breathing better after DuoNeb nebulizer therapy, wheezing decreased"
      }},
      {{
        "event": "Patient stable and ready for discharge",
        "time": "By discharge (~23:00 EDT)",
        "details": "Respiratory symptoms improved, patient requesting discharge, son available to collect her"
      }}
    ],
    "narrative_summary": "85-year-old female with severe COPD and oxygen dependence presented to ED after chemical fume exposure from melting plastic spice rack. She had been seen earlier the same day for COPD exacerbation and started on Decadron. Physical exam showed mild wheezing, chest X-ray was negative for acute process, and she improved with bronchodilator therapy. Discharged home stable after approximately 1.5 hours with follow-up instructions.",
    "disposition": "discharged_home",
    "length_of_stay": "Approximately 1.5 hours",
    "patient_response": "Patient's respiratory status improved after nebulizer therapy. By discharge, she was breathing better and symptoms had resolved.",
    "admission_date": "2025-08-29",
    "discharge_date": "2025-08-29",
    "follow_up_plans": [
      "Follow up with PCP Dr. Byland within 24-48 hours",
      "Return to ER or call 911 if condition changes or worsens",
      "Continue home medications as prescribed",
      "Take antibiotics as prescribed"
    ]
  }},
  "patient_id": "10838402",
  "hospitalization_id": "4002138129"
}}
```

### Example 2: Trauma with Fall
```json
{{
  "hospital_course": {{
    "timeline": [
      {{
        "event": "Presented to ED by EMS after fall at home",
        "time": "On arrival",
        "details": "Patient reports dizziness when standing, then fell forward striking head on counter"
      }},
      {{
        "event": "CT head completed",
        "time": "During ED stay",
        "details": "Result: No acute intracranial injury, chronic ischemic changes noted"
      }},
      {{
        "event": "Symptoms improved with supportive care",
        "time": "During observation",
        "details": "Dizziness resolved, headache improved, patient felt better"
      }},
      {{
        "event": "Patient at baseline and cleared for discharge",
        "time": "By discharge",
        "details": "All symptoms resolved, ambulatory without issues"
      }}
    ],
    "narrative_summary": "72-year-old male presented to ED by EMS after fall at home with head injury. Patient reported dizziness when standing followed by fall. CT head negative for acute injury. Symptoms improved with supportive care and patient was discharged home with fall prevention counseling.",
    "disposition": "discharged_home",
    "length_of_stay": "Same day ED visit",
    "patient_response": "Patient felt significantly better after observation period, symptoms resolved by discharge",
    "admission_date": "2025-07-31",
    "discharge_date": "2025-07-31",
    "follow_up_plans": [
      "Follow up with PCP within 1 week",
      "Return if symptoms recur or worsen",
      "Fall prevention counseling provided"
    ]
  }},
  "patient_id": "12345678",
  "hospitalization_id": "9876543210"
}}
```

### Example 3: Inpatient Admission
```json
{{
  "hospital_course": {{
    "timeline": [
      {{
        "event": "Admitted with acute kidney injury and metabolic acidosis",
        "time": "2025-10-15",
        "details": "Creatinine 2.4 (baseline 1.1), lactate 4.2 mmol/L, pH 7.28"
      }},
      {{
        "event": "Clinical improvement noted",
        "time": "Hospital Day 2",
        "details": "Creatinine improving to 1.8, lactate decreasing, mental status clearer"
      }},
      {{
        "event": "Labs normalized",
        "time": "Hospital Day 3",
        "details": "Creatinine 1.3 (near baseline), lactate normal, pH 7.38"
      }},
      {{
        "event": "Patient at baseline and cleared for discharge",
        "time": "Hospital Day 3",
        "details": "Stable, tolerating oral intake, ambulating independently"
      }}
    ],
    "narrative_summary": "Patient admitted with acute kidney injury and lactic acidosis, likely secondary to metformin in setting of declining renal function. Improved with IV fluid resuscitation and supportive care. Labs normalized by Hospital Day 3 and patient was discharged home with nephrology follow-up.",
    "disposition": "discharged_home_with_services",
    "length_of_stay": "3 days",
    "patient_response": "Excellent response to treatment with complete resolution of AKI and acidosis by day 3",
    "admission_date": "2025-10-15",
    "discharge_date": "2025-10-18",
    "follow_up_plans": [
      "Nephrology follow-up in 1 week",
      "Repeat BMP in 3-5 days",
      "Continue medication adjustments as prescribed",
      "Avoid metformin until cleared by nephrologist"
    ]
  }},
  "patient_id": "87654321",
  "hospitalization_id": "1234567890"
}}
```

---

## Critical Reminders

1. ✅ **Patient ID**: Extract MRN (8-10 digits), NOT document/RRD numbers
2. ✅ **Timeline**: 5-10 events covering full encounter including prior same-day visits
3. ✅ **Status-focused**: Patient progression, not individual treatments
4. ✅ **Actual timestamps**: Use when available (YYYY-MM-DD HH:MM EDT)
5. ✅ **Narrative**: 2-4 sentences in prose format
6. ✅ **Follow-up**: Extract all documented follow-up instructions
7. ✅ **Dates**: YYYY-MM-DD format for admission/discharge
8. ❌ **Don't infer**: Extract only documented information

---

Return ONLY the JSON. No explanations or additional text.
'''

__all__ = ["system_prompt", "course_prompt"]
