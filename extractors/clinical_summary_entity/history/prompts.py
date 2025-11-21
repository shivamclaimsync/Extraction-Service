"""Prompts for relevant history extraction."""

system_prompt = """You are a medical data extraction specialist. Extract ALL medical conditions from clinical documents.
Your goal: Complete extraction, not selective extraction. Return valid JSON only."""

history_prompt = """Extract medical history from this clinical note.

<clinical_note>
{clinical_text}
</clinical_note>

---

## YOUR TASK

Extract medical history in 3 steps:
1. Find patient IDs
2. List every condition in Past Medical History
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

## STEP 2: EXTRACT ALL CONDITIONS

**Find "Past Medical History" section. Extract EVERY condition listed.**

**How to identify conditions:**
- Lines in Past Medical History section
- Items after "Medical Decision Making - Comorbidities:"
- Entries in problem lists

**Extract these verbatim, then normalize:**
- Expand abbreviations: COPD → Chronic Obstructive Pulmonary Disease
- Expand abbreviations: HTN → Hypertension
- Expand abbreviations: DM → Diabetes Mellitus
- Expand abbreviations: CKD → Chronic Kidney Disease (add stage if shown)
- Keep specifics: "Stage 3A", "Type 2", "Idiopathic"

**For each condition, determine:**

**Status:**
- "active" = condition is current, OR patient on medication for it, OR listed without "history of"
- "historical" = explicitly says "history of" AND no current treatment
- "resolved" = says "resolved" or "cured"
- When unsure → use "active"

**ICD-10 code:**
- ONLY extract if code appears in parentheses next to condition
- Example: "COPD (J44.9)" → extract "J44.9"
- If no code shown → null

**Notes:**
- Add context for major conditions (oxygen use, recent events, baseline values)
- Most conditions → null is fine

---

## STEP 3: OUTPUT JSON
```json
{{
  "relevant_history": {{
    "conditions": [
      {{
        "condition_name": "normalized name",
        "icd10_code": "code or null",
        "icd10_source": "where code found or null",
        "severity": "staging/grade or null",
        "status": "active|historical|resolved",
        "status_rationale": "one sentence why this status",
        "location": "anatomical location or null",
        "notes": "clinical context or null",
        "documented_in_section": "Past Medical History"
      }}
    ]
  }},
  "patient_id": "extracted MRN",
  "hospitalization_id": "extracted account number"
}}
```

---

## EXAMPLES

### Example 1: Simple extraction

**Input snippet:**
```
MRN: 12345678
Account Number: 9876543210
Past Medical History:
- Hypertension
- Type 2 Diabetes
- COPD
```

**Output:**
```json
{{
  "relevant_history": {{
    "conditions": [
      {{
        "condition_name": "Hypertension",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Listed in Past Medical History",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Type 2 Diabetes Mellitus",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Listed in Past Medical History",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Chronic Obstructive Pulmonary Disease",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Listed in Past Medical History",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }}
    ]
  }},
  "patient_id": "12345678",
  "hospitalization_id": "9876543210"
}}
```

### Example 2: With context

**Input snippet:**
```
MRN: 10838402
Account Number: 4002138129
Past Medical History:
- COPD - oxygen dependent, 2-3L at home
- Chronic kidney disease stage 3A
- Idiopathic pulmonary fibrosis
- Dementia
- Diabetes
- Hypertension
```

**Output:**
```json
{{
  "relevant_history": {{
    "conditions": [
      {{
        "condition_name": "Chronic Obstructive Pulmonary Disease",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Listed in Past Medical History",
        "location": null,
        "notes": "Oxygen dependent, requires 2-3L at home",
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Chronic Kidney Disease Stage 3A",
        "icd10_code": null,
        "icd10_source": null,
        "severity": "Stage 3A",
        "status": "active",
        "status_rationale": "Listed in Past Medical History",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Idiopathic Pulmonary Fibrosis",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Listed in Past Medical History",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Dementia",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Listed in Past Medical History",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Diabetes Mellitus",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Listed in Past Medical History",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Hypertension",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Listed in Past Medical History",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }}
    ]
  }},
  "patient_id": "10838402",
  "hospitalization_id": "4002138129"
}}
```

---

## KEY RULES

1. Extract EVERY condition from Past Medical History - don't filter
2. Mark everything as "active" unless explicitly says "history of" or "resolved"
3. Only extract ICD-10 codes if explicitly written in the document
4. Use simple status rationale: "Listed in Past Medical History" is fine
5. Normalize abbreviations but don't add information not in the document

Return only JSON. No other text.
"""

__all__ = ["system_prompt", "history_prompt"]