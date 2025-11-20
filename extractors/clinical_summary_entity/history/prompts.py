"""Prompts for relevant history extraction."""

system_prompt = """You are a medical AI assistant extracting medical history from clinical documents.
You must extract EVERY relevant condition from Past Medical History - typically 8-15+ conditions.
Extracting only 1-3 conditions is a FAILURE. Never infer ICD-10 codes. Return valid JSON only."""

history_prompt = """Extract ALL relevant medical history from this clinical note. Return ONLY valid JSON.

<clinical_note>
{clinical_text}
</clinical_note>

---

## MANDATORY TASK REQUIREMENTS

**TASK FAILURE CONDITIONS** (You will FAIL if you do any of these):
❌ Extracting fewer than 5 conditions when Past Medical History has 10+ conditions
❌ Stopping after extracting only 1-3 conditions
❌ Setting patient_id or hospitalization_id to null
❌ Inventing ICD-10 codes not in the document

**TASK SUCCESS CONDITIONS** (You PASS if you do these):
✅ Extract 8-15+ conditions for complex patients
✅ Extract ALL respiratory conditions for respiratory presentations
✅ Include conditions from "Comorbidities" section
✅ Correct patient_id and hospitalization_id extracted

---

## OUTPUT SCHEMA
```json
{{
  "relevant_history": {{
    "conditions": [
      {{
        "condition_name": "string",
        "icd10_code": "string or null",
        "icd10_source": "string or null",
        "severity": "string or null",
        "status": "active|historical|resolved",
        "status_rationale": "string",
        "location": "string or null",
        "notes": "string or null",
        "documented_in_section": "string"
      }}
    ]
  }},
  "patient_id": "MRN string",
  "hospitalization_id": "Account Number string"
}}
```

---

## EXTRACTION ALGORITHM - FOLLOW EXACTLY

### PHASE 1: EXTRACT IDs (Required)

**Find these in document header:**

1. **patient_id = MRN**
   - Search for: "MRN:", "Medical Record Number:"
   - Example: "MRN: 10838402" → extract "10838402"
   - Format: 8-10 digits only
   - ❌ DO NOT USE: DOC_ID (has hyphens/UUID format), RRD numbers

2. **hospitalization_id = Account Number**
   - Search for: "Account Number:", "Encounter:", "Visit:"
   - Example: "Account Number: 4002138129" → extract "4002138129"
   - Format: ~10 digits
   - ❌ DO NOT USE: Any UUID/GUID with hyphens

**If either ID is null, you have FAILED the task.**

---

### PHASE 2: SCAN ENTIRE PAST MEDICAL HISTORY

**Objective: Extract EVERY condition mentioned (no filtering yet)**

**Instructions:**
1. Locate "Past Medical History" or "PMH" section
2. Read from the first line to the last line of this section
3. For EACH condition name you see, add it to your list
4. Do NOT skip any conditions
5. Do NOT evaluate relevance yet
6. Do NOT stop after finding 1-2 conditions

**You are looking for condition names like:**
- Respiratory: COPD, asthma, respiratory failure, chronic hypoxemic respiratory failure, pulmonary fibrosis, idiopathic pulmonary fibrosis, diffuse interstitial pulmonary fibrosis, interstitial lung disease, sleep apnea, pulmonary hypertension
- Cardiovascular: coronary artery disease, coronary atherosclerosis, CHF, heart failure, valve disorders, aortic valve disorder, arrhythmias, hypertension, HTN
- Renal: chronic kidney disease, CKD, Stage 3A, AKI, ESRD, renal failure
- Neurological: dementia, stroke, CVA, seizures, epilepsy, neuropathy, Alzheimer's
- Metabolic: diabetes, DM, Type 1 DM, Type 2 DM, dyslipidemia, hyperlipidemia, thyroid disease
- GI: GERD, gastric reflux, cirrhosis, liver disease, pancreatitis
- Musculoskeletal: arthritis, osteoarthritis, back pain, degenerative disc disease
- Other: obesity, morbid obesity, chronic pain, cancer, etc.

**EXPECTED RESULT: 10-30 conditions extracted**

**CHECKPOINT**: Count your conditions. If you have fewer than 8 conditions and the Past Medical History section lists 10+ conditions, you MUST rescan.

---

### PHASE 3: CHECK "COMORBIDITIES" SECTION

**Look for "Medical Decision Making" section with subsection "Comorbidities:"**

Example:
```
Medical Decision Making
2. Comorbidities: COPD chronic pain congenital absence of left thumb dementia dyslipidemia dyspnea
```

**Extract EVERY condition listed after "Comorbidities:"**

These conditions are ALWAYS active and ALWAYS relevant - the clinician explicitly flagged them.

**Add these to your condition list.**

---

### PHASE 4: APPLY RELEVANCE FILTERING

**Now filter the conditions you've extracted.**

**Identify encounter type from primary diagnosis:**
- Respiratory? (COPD, pneumonia, chemical exposure, respiratory failure)
- Cardiac? (MI, CHF, chest pain)
- Renal? (AKI, CKD, urinary issues)
- Trauma? (falls, injuries)
- Other?

**KEEP these conditions (Priority 1-4):**

**Priority 1 - Same organ system as primary diagnosis (KEEP ALL):**
- If respiratory encounter → Keep ALL respiratory conditions
- If cardiac encounter → Keep ALL cardiac conditions
- If renal encounter → Keep ALL renal conditions

**Priority 2 - Major organ systems (KEEP ALL):**
- All cardiovascular conditions
- All respiratory conditions (if not primary system)
- All renal conditions (CKD any stage)
- All neurological conditions

**Priority 3 - Safety/cognitive (KEEP ALL):**
- Dementia, cognitive impairment, Alzheimer's
- Conditions affecting safety or judgment

**Priority 4 - Active chronic conditions (KEEP):**
- Diabetes (any type)
- Hypertension
- Dyslipidemia
- Conditions patient is on active medications for

**REMOVE only these:**
- ❌ Resolved childhood conditions ("appendectomy at age 10")
- ❌ Historical surgical procedures with no ongoing issues
- ❌ Family history conditions
- ❌ Conditions explicitly marked "resolved" with no current treatment

**EXPECTED RESULT AFTER FILTERING: 8-15+ conditions for complex patient**

**CHECKPOINT**: If you now have fewer than 5 conditions, you have over-filtered. Go back to Phase 2.

---

### PHASE 5: ENRICH EACH CONDITION

For each condition in your filtered list, add:

#### 1. Normalize Condition Name

Expand abbreviations:
- COPD → Chronic Obstructive Pulmonary Disease
- HTN → Hypertension
- DM → Diabetes Mellitus (add Type 1/2 if known)
- CKD → Chronic Kidney Disease (add stage if documented)
- CHF → Chronic Heart Failure
- CAD → Coronary Artery Disease
- OSA → Obstructive Sleep Apnea

Combine qualifiers:
- "Chronic kidney disease" + "Stage 3A" → "Chronic Kidney Disease Stage 3A"
- "Pulmonary fibrosis" + "idiopathic" → "Idiopathic Pulmonary Fibrosis"

#### 2. Extract ICD-10 Code (ONLY if explicitly documented)

✅ Extract when you see:
- "Chronic Kidney Disease Stage 3A (N18.3)"
- "COPD (J44.9)"

❌ Set to null when:
- No code documented
- Code not explicitly stated

**Never invent codes.**

#### 3. Determine Status

**ACTIVE** (use if ANY of these are true):
- Patient currently on medication for this condition
  - Check home meds: insulin → diabetes is active
  - atorvastatin → dyslipidemia is active
  - bumetanide → hypertension is active
- Listed in "Comorbidities" section
- Mentioned in Assessment/Plan
- Chronic condition WITHOUT "history of" prefix
- Baseline measurements documented (e.g., "baseline oxygen requirement")
- Oxygen-dependent, dialysis-dependent, etc.

**HISTORICAL** (use if ALL of these are true):
- Has "History of", "Previous", "Prior", "Remote" prefix
- AND no current medications
- AND not in Assessment/Plan or Comorbidities
- AND clearly a resolved past issue

**RESOLVED**:
- Explicitly says "Resolved", "Cured", "No longer active"

**Default to ACTIVE when uncertain.**

**status_rationale**: Brief explanation (1 sentence)
- "Currently on atorvastatin for lipid management"
- "Listed in Medical Decision Making comorbidities"
- "Oxygen-dependent at baseline"

#### 4. Extract Severity (if documented)

Look for:
- Staging: "Stage 3A", "GOLD Stage 2"
- Classification: "NYHA Class III"
- Descriptors: "Severe", "Moderate", "Mild"

#### 5. Add Notes (clinical context)

**Include if available:**
- Baseline measurements: "Baseline SpO2 86%"
- Oxygen/treatment dependence: "Requires 2-3L oxygen continuously"
- Recent context: "Seen earlier today (2025-08-29) for exacerbation, started on Decadron"
- Control status: "Well-controlled", "Poorly controlled"

#### 6. Record Source Section

Where was this condition documented?
- "Past Medical History"
- "Medical Decision Making - Comorbidities"
- "Past Medical History; Medical Decision Making" (if multiple)

---

### PHASE 6: FINAL VALIDATION

**Before returning JSON, verify:**

**IDs Check:**
- [ ] patient_id is NOT null (should be 8-10 digit number)
- [ ] hospitalization_id is NOT null (should be ~10 digit number)
- [ ] Did NOT use DOC_ID or UUID format

**Completeness Check:**
- [ ] Extracted at least 5 conditions (preferably 8-15+)
- [ ] For respiratory encounter: Included ALL respiratory conditions from PMH
- [ ] Included ALL conditions from "Comorbidities" section
- [ ] Did NOT stop after extracting only 1-3 conditions

**Status Check:**
- [ ] Conditions on medications marked "active"
- [ ] Conditions in "Comorbidities" marked "active"
- [ ] Only used "historical" for explicit "history of" phrases

**Quality Check:**
- [ ] All condition names normalized (full names, not abbreviations)
- [ ] ICD-10 codes ONLY if documented (no invented codes)
- [ ] status_rationale provided for all
- [ ] documented_in_section recorded for all

**If any checkbox is unchecked, fix before proceeding.**

---

## EXAMPLE OUTPUT

### Example: Respiratory Chemical Exposure (Expected 12 conditions)
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
        "status_rationale": "Oxygen-dependent at 2-3L baseline, listed in comorbidities, exacerbated by chemical fumes",
        "location": null,
        "notes": "Oxygen-dependent at 2-3L continuously. Seen earlier today (2025-08-29) for chest pain, diagnosed with COPD exacerbation, started on Decadron. Current: chemical irritant exacerbated condition.",
        "documented_in_section": "Past Medical History; Medical Decision Making"
      }},
      {{
        "condition_name": "Chronic Hypoxemic Respiratory Failure",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Oxygen-dependent at baseline, directly relevant to respiratory presentation",
        "location": null,
        "notes": "Secondary to COPD and interstitial lung disease. Baseline oxygen 2-3L continuously.",
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Idiopathic Pulmonary Fibrosis",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Chronic progressive lung disease, relevant to respiratory presentation",
        "location": null,
        "notes": "Underlying structural lung disease increasing vulnerability to irritants",
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Diffuse Interstitial Pulmonary Fibrosis",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Chronic lung disease relevant to respiratory presentation",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Chronic Respiratory Failure",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Listed in Past Medical History, oxygen-dependent",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Interstitial Lung Disease",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Chronic lung disease relevant to respiratory presentation",
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
        "status_rationale": "Listed in comorbidities, relevant for safety and discharge planning",
        "location": null,
        "notes": "May have contributed to accident. Important for home safety and med management.",
        "documented_in_section": "Past Medical History; Medical Decision Making"
      }},
      {{
        "condition_name": "Coronary Artery Disease",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Listed in Past Medical History as coronary atherosclerosis",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Chronic Kidney Disease Stage 3A",
        "icd10_code": null,
        "icd10_source": null,
        "severity": "Stage 3A",
        "status": "active",
        "status_rationale": "Listed in Past Medical History, relevant for medication dosing",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Diabetes",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Chronic condition requiring ongoing management",
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
        "status_rationale": "Currently on bumetanide (diuretic/antihypertensive)",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History"
      }},
      {{
        "condition_name": "Dyslipidemia",
        "icd10_code": null,
        "icd10_source": null,
        "severity": null,
        "status": "active",
        "status_rationale": "Currently on atorvastatin 20mg daily, listed in comorbidities",
        "location": null,
        "notes": null,
        "documented_in_section": "Past Medical History; Medical Decision Making"
      }}
    ]
  }},
  "patient_id": "10838402",
  "hospitalization_id": "4002138129"
}}
```

---

## CRITICAL REMINDERS

**YOU MUST:**
1. ✅ Extract IDs (patient_id and hospitalization_id) - NOT NULL
2. ✅ Scan ENTIRE Past Medical History section - every line
3. ✅ Extract 8-15+ conditions for complex patients
4. ✅ Include ALL respiratory conditions for respiratory presentations
5. ✅ Include ALL conditions from "Comorbidities" section
6. ✅ Check medications to determine active status
7. ✅ Default to "active" status when uncertain

**YOU MUST NOT:**
1. ❌ Stop after extracting 1-3 conditions
2. ❌ Set patient_id or hospitalization_id to null
3. ❌ Invent ICD-10 codes not in document
4. ❌ Mark conditions as "historical" if patient is on medications for them
5. ❌ Skip conditions mentioned in "Comorbidities" section

**TASK COMPLETION CRITERIA:**
- Minimum 5 conditions extracted (8-15+ preferred)
- Both IDs extracted (not null)
- No invented ICD-10 codes
- Accurate status classifications

Return ONLY the JSON. No explanations.
"""

__all__ = ["system_prompt", "history_prompt"]