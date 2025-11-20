"""Concise prompts for diagnosis extraction."""

system_prompt = """You are a medical data extraction AI. Extract diagnosis information exactly as documented. 

Never infer ICD-10 codes. Never hallucinate. Extract only what's explicitly written."""

diagnosis_prompt = '''Extract diagnosis information from this clinical note and return ONLY valid JSON.

**Core Principle**: Extract only explicitly documented information. Do NOT infer, assume, or invent diagnoses or ICD-10 codes.

<clinical_note>
{clinical_text}
</clinical_note>

---

## Output Schema

```json
{{
  "diagnosis": {{
    "primary_diagnosis": "exact text from note (required)",
    "primary_diagnosis_icd10": "code or null (ONLY if documented)",
    "primary_diagnosis_evidence": "Section: \"quote\" (required)",
    "diagnosis_category": "category (required)",
    "secondary_diagnoses": [
      {{
        "diagnosis": "exact text",
        "icd10_code": "code or null",
        "evidence": "Section: \"quote\"",
        "relationship_to_primary": "relationship type"
      }}
    ]
  }}
}}
```

---

## Extraction Rules

### Primary Diagnosis

**Where to Look** (in priority order):
1. Discharge/Final Diagnosis (first listed)
2. This Visit Problems (first listed)
3. Assessment/Plan (main diagnosis)
4. Medical Decision Making (for ED visits)
5. Chief Complaint (only if no formal diagnosis documented)

**What to Extract**:
- Exact wording (verbatim, no paraphrasing)
- ICD-10 code ONLY if written next to diagnosis (format: Letter + 2-7 chars, e.g., N17.9, E11.65)
- Evidence: `"Section Name: \"exact quote\""`
- Category: cardiovascular, renal, respiratory, neurological, gastrointestinal, endocrine, infectious, musculoskeletal, psychiatric, trauma, environmental, other

**Category Selection**:
- Base on PRIMARY diagnosis only
- For infectious organ dysfunction, prefer organ system (pneumonia → respiratory, not infectious)
- Use "environmental" for non-medical presentations (power outage, social issues)

**Special Cases**:
- No formal diagnosis: Use chief complaint, set ICD-10 to null, note in evidence
- ED visits: Presenting complaint often is primary diagnosis even if workup negative

### Secondary Diagnoses

**Include if** (meet ANY):
- Numbered in Discharge/Final Diagnosis (beyond #1)
- Listed in Assessment/Plan with active management
- In Medical Decision Making → "Comorbidities:" subsection
- In This Visit Problems (beyond #1)
- Explicitly mentioned as influencing current care
- Acute exacerbation of chronic condition

**Exclude**:
- Past Medical History ONLY (not mentioned elsewhere)
- Inactive/resolved conditions
- Family/social history
- Stable conditions not discussed in Assessment/Plan
- Entire PMH dump

**For Each Secondary Diagnosis**:
- Extract exact wording (verbatim)
- ICD-10 code ONLY if documented (else null)
- Evidence: `"Section Name: \"exact quote\""`
- Relationship: "complication of", "contributing factor", "pre-existing condition", "acute exacerbation", "unrelated", or null

**Relationship Definitions**:
- **complication of**: Directly caused by primary (e.g., lactic acidosis from metformin in AKI)
- **contributing factor**: Pre-existing condition that contributed (e.g., CKD contributing to AKI)
- **pre-existing condition**: Relevant chronic condition, not directly causal (e.g., diabetes in head injury admission)
- **acute exacerbation**: Chronic condition that acutely worsened
- **unrelated**: Independent active condition managed during visit
- **null**: Relationship unclear

---

## Evidence Format

Always use: `"Section Name: \"verbatim quote from note\""`

**Good Examples**:
- `"Discharge Diagnosis: \"1. Acute kidney injury (N17.9)\""`
- `"Assessment and Plan: \"Patient admitted with pneumonia, will treat with antibiotics\""`

**Bad Examples**:
- `"Found in the note"` ❌ (too vague)
- `"Patient has diabetes"` ❌ (not a direct quote)

---

## Validation Checklist

Before returning JSON, verify:
- [ ] Primary diagnosis is verbatim quote with evidence
- [ ] ICD-10 codes ONLY if explicitly documented (no invented codes)
- [ ] Category matches primary diagnosis
- [ ] Secondary diagnoses relevant to THIS encounter (not entire PMH)
- [ ] All diagnoses have evidence with section name + quote
- [ ] Relationship classification provided for all secondary diagnoses

---

## Examples

**Example 1: ED Visit with Comorbidities**
```json
{{
  "diagnosis": {{
    "primary_diagnosis": "Respiratory condition due to chemical fumes",
    "primary_diagnosis_icd10": null,
    "primary_diagnosis_evidence": "This Visit Problems: \"1. Respiratory condition due to chemical fumes, 2025-08-29\"",
    "diagnosis_category": "respiratory",
    "secondary_diagnoses": [
      {{
        "diagnosis": "COPD",
        "icd10_code": null,
        "evidence": "Medical Decision Making: \"Comorbidities: COPD chronic pain congenital absence of left thumb dementia dyslipidemia dyspnea\"",
        "relationship_to_primary": "pre-existing condition"
      }},
      {{
        "diagnosis": "Exacerbation of COPD",
        "icd10_code": null,
        "evidence": "History of Present Illness: \"She was seen earlier in the ER today for chest pain she was diagnosed with exacerbation of COPD she was started on Decadron\"",
        "relationship_to_primary": "acute exacerbation"
      }}
    ]
  }}
}}
```

**Example 2: Inpatient with ICD-10 Codes**
```json
{{
  "diagnosis": {{
    "primary_diagnosis": "Acute kidney injury",
    "primary_diagnosis_icd10": "N17.9",
    "primary_diagnosis_evidence": "Discharge Diagnosis: \"1. Acute kidney injury (N17.9)\"",
    "diagnosis_category": "renal",
    "secondary_diagnoses": [
      {{
        "diagnosis": "Type 2 Diabetes Mellitus",
        "icd10_code": "E11.9",
        "evidence": "Discharge Diagnosis: \"2. Type 2 Diabetes Mellitus (E11.9)\"",
        "relationship_to_primary": "contributing factor"
      }}
    ]
  }}
}}
```

**Example 3: Primary Only**
```json
{{
  "diagnosis": {{
    "primary_diagnosis": "Chest pain, rule out MI",
    "primary_diagnosis_icd10": null,
    "primary_diagnosis_evidence": "Assessment: \"Chest pain, low risk, rule out MI. Troponins negative x2.\"",
    "diagnosis_category": "cardiovascular",
    "secondary_diagnoses": []
  }}
}}
```

---

Return ONLY the JSON object. No explanations or additional text.
'''

__all__ = ["system_prompt", "diagnosis_prompt"]
