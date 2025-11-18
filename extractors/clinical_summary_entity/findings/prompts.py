"""Prompts for clinical findings extraction."""

system_prompt = """
You are a medical AI assistant specializing in clinical findings extraction from clinical documents.

Your role is to accurately extract laboratory results, vital signs, physical exam findings, imaging 
results, and anthropometric measurements exactly as documented, prioritizing clinically significant 
abnormalities. You must not hallucinate clinical significance or infer findings beyond what is stated.

Follow all task instructions precisely and respond only in valid JSON format.
"""

findings_prompt = """
You are analyzing clinical documents to extract clinical findings. Your extraction must prioritize 
clinically significant abnormalities while adhering strictly to documented evidence.

## Core Principles

### EXTRACTION NOT INFERENCE
**START HERE**: Extract only documented findings. Do NOT infer clinical significance not stated.

You will be PENALIZED for:
- Hallucinating clinical significance not documented
- Including every normal finding (prioritize abnormals)
- Misclassifying lab status (critical vs abnormal vs normal)
- Inferring baseline values not explicitly stated
- Over-interpreting imaging findings

You will be REWARDED for:
- Prioritizing clinically significant abnormalities
- Accurate status classification with objective criteria
- Extracting only documented clinical significance
- Appropriate null usage for missing data
- Clear documentation of sources

---

## PRIORITIZATION RULE: Significant Over Comprehensive

**PRIORITY**: Extract abnormal/critical findings first. Include normal findings only when:
1. Explicitly discussed in Assessment/Plan
2. Rule-out significant (e.g., "Troponin negative" for chest pain)
3. Baseline/monitoring context (e.g., "Creatinine stable at baseline")

❌ **DO NOT** dump every normal lab value or exam finding.

---

## Step 1: Extract Laboratory Results

### Locate Lab Sections:
- **Laboratory Results** / **Labs**
- **Blood Work**
- **Chemistry** / **Hematology** / **Coagulation**
- **ABG** (Arterial Blood Gas)
- **Urinalysis**

### Prioritization (extract in this order):

**Tier 1: CRITICAL VALUES** (always extract)
- Life-threatening abnormalities requiring immediate action
- pH <7.30 or >7.50
- Lactate >4.0 mmol/L
- K+ <2.5 or >6.0 mmol/L
- Glucose <40 or >400 mg/dL
- Creatinine >3.0 mg/dL with acute change
- Hgb <7 g/dL or >18 g/dL
- WBC <2.0 or >20.0 x10^9/L
- Troponin elevation in cardiac presentation

**Tier 2: SIGNIFICANT ABNORMALS** (extract if discussed)
- Values outside reference range AND mentioned in Assessment/Plan
- Organ function markers showing impairment (Cr, BUN, AST, ALT, bilirubin)
- Acute changes from baseline (≥50% change)
- Electrolyte abnormalities (Na, K, Cl, Ca, Mg)

**Tier 3: BASELINE/MONITORING VALUES** (extract selectively)
- Baseline values explicitly stated (e.g., "Baseline creatinine 1.2")
- Monitoring values showing stability or improvement
- Rule-out negatives (e.g., "Troponin negative")

**SKIP**: Routine normals not discussed (e.g., CBC components all normal, routine normals)

### Lab Test Extraction Format:

**id**: Sequential identifier (lab_001, lab_002, ...)

**test_name**: Normalized name
- Use standard names: "Creatinine", "BUN", "Sodium", "Potassium", "White Blood Cell Count"
- Expand abbreviations: "Cr" → "Creatinine", "K+" → "Potassium", "Hgb" → "Hemoglobin"

**test_category**: Assign category
- chemistry, hematology, coagulation, arterial_blood_gas, urinalysis, metabolic, cardiac, hepatic, renal, electrolytes, endocrine, toxicology

**value**: Numeric or string as documented

**unit**: Extract unit (mg/dL, mmol/L, g/dL, etc.)

**status**: Classify status using these criteria:
- **critical**: Life-threatening or requiring immediate intervention
- **abnormal_high**: Above reference range (not critical)
- **abnormal_low**: Below reference range (not critical)
- **normal**: Within reference range

**reference_range**: Extract if documented (e.g., "0.6-1.2")
- Also populate reference_range_min and reference_range_max if numeric

**baseline_value**: Extract ONLY if explicitly documented (e.g., "Baseline Cr 1.2")

**clinical_significance**: Extract ONLY if explicitly stated in the note
- ✅ "Creatinine elevated indicating acute kidney injury"
- ✅ "Lactate elevation consistent with lactic acidosis"
- ❌ DO NOT infer significance

**documented_in_section**: Source section (e.g., "Laboratory Results", "ABG")

### Example:

```json
{{
  "id": "lab_001",
  "test_name": "Creatinine",
  "test_category": "renal",
  "value": 2.4,
  "unit": "mg/dL",
  "status": "abnormal_high",
  "reference_range": "0.6-1.2",
  "reference_range_min": 0.6,
  "reference_range_max": 1.2,
  "baseline_value": 1.1,
  "clinical_significance": "Elevated creatinine indicating acute kidney injury",
  "documented_in_section": "Laboratory Results"
}}
```

---

## Step 2: Extract Vital Signs

### Locate Sections:
- **Vital Signs**
- **Triage** (for ED notes)
- **Physical Exam** (may include vitals)

### Vital Signs to Extract (prioritize abnormals):

**Always extract**:
- Blood Pressure (if abnormal or relevant)
- Heart Rate (if abnormal or relevant)
- Respiratory Rate (if abnormal or relevant)
- Temperature (if fever or hypothermia)
- Oxygen Saturation (SpO2) - especially if low
- Oxygen Requirements (e.g., "2L NC", "Room air")

**Vital Sign Status Classification**:
- **abnormal_high**: BP >140/90, HR >100, RR >20, Temp >38°C
- **abnormal_low**: BP <90/60, HR <60, RR <12, SpO2 <92%
- **normal**: Within normal limits

**clinical_significance**: Only if explicitly documented
- ✅ "Hypotension requiring fluid resuscitation"
- ✅ "Tachycardia consistent with dehydration"
- ❌ DO NOT infer

### Example:

```json
{{
  "measurement": "Blood Pressure",
  "value": "107/69",
  "unit": "mmHg",
  "status": "normal",
  "clinical_significance": null
}}
```

---

## Step 3: Extract Physical Exam Findings

### Locate Sections:
- **Physical Exam** / **Physical Examination**
- **HEENT**
- **Cardiovascular**
- **Respiratory**
- **Neurological**
- etc.

### Prioritization:

**EXTRACT**:
- Abnormal findings (injuries, pathology, notable abnormalities)
- Positive pertinent findings relevant to presentation
- Explicitly discussed normals ("Neuro exam intact", "No focal deficits")

**SKIP**:
- Routine normal findings not discussed ("Normal S1/S2", "Clear to auscultation" if not relevant)

### Format:

**system**: Body system (HEENT, Cardiovascular, Respiratory, Abdominal, Musculoskeletal, Neurological, Skin, Extremities)

**finding**: Description of the finding as documented

**status**: normal or abnormal

### Examples:

```json
[
  {{
    "system": "HEENT",
    "finding": "Forehead contusion with minor abrasion",
    "status": "abnormal"
  }},
  {{
    "system": "Neurological",
    "finding": "Alert and oriented, no focal neurological deficits",
    "status": "normal"
  }},
  {{
    "system": "Respiratory",
    "finding": "Diffuse crackles bilaterally",
    "status": "abnormal"
  }}
]
```

---

## Step 4: Extract Imaging Findings

### Locate Sections:
- **Diagnostic Results** / **Imaging**
- **Radiology**
- **CT** / **MRI** / **X-ray** / **Ultrasound**

### Imaging Study Extraction:

**study**: Full name of study (e.g., "CT Head without contrast", "Chest X-ray")

**date**: Date of study if documented

**findings**: List of specific findings (prioritize abnormalities)
- Abnormal findings
- Negative findings if rule-out significant (e.g., "No acute intracranial hemorrhage")
- Chronic/incidental findings if discussed

**impression**: Radiologist's impression or summary (direct quote or close paraphrase)

### Example:

```json
{{
  "study": "CT Head without contrast",
  "date": "2025-06-10",
  "findings": [
    "No acute intracranial injury",
    "Chronic ischemic changes",
    "Age-appropriate cerebral atrophy"
  ],
  "impression": "No acute intracranial injury. Chronic ischemic changes and age-appropriate atrophy."
}}
```

---

## Step 5: Extract Anthropometrics

### Locate in:
- **Physical Exam**
- **Vital Signs**
- **Triage**

### Measurements:

**height**: 
```json
{{
  "value": 160,
  "unit": "cm",
  "notes": null
}}
```

**weight**:
```json
{{
  "value": 167,
  "unit": "kg",
  "notes": "Lost 70 pounds recently"
}}
```

**bmi**:
```json
{{
  "value": 61.4,
  "unit": "kg/m²",
  "notes": "Morbid obesity"
}}
```

**When to use null**: If measurement not documented, set entire field to null.

---

## JSON Output Schema

```json
{{
  "clinical_findings": {{
    "lab_results": [
      {{
        "id": "lab_001",
        "test_name": "string",
        "test_category": "chemistry|hematology|coagulation|arterial_blood_gas|urinalysis|metabolic|cardiac|hepatic|renal|electrolytes|endocrine|toxicology",
        "value": "string or numeric",
        "unit": "string or null",
        "status": "critical|abnormal_high|abnormal_low|normal",
        "reference_range": "string or null",
        "reference_range_min": numeric or null,
        "reference_range_max": numeric or null,
        "baseline_value": "string or numeric or null",
        "clinical_significance": "string or null",
        "documented_in_section": "string or null"
      }}
    ],
    "vital_signs": [
      {{
        "measurement": "string",
        "value": "string or numeric",
        "unit": "string or null",
        "status": "normal|abnormal_high|abnormal_low|null",
        "clinical_significance": "string or null"
      }}
    ] or null,
    "physical_exam_findings": [
      {{
        "system": "string",
        "finding": "string",
        "status": "normal|abnormal|null"
      }}
    ] or null,
    "imaging_findings": [
      {{
        "study": "string",
        "date": "string or null",
        "findings": ["array of strings"],
        "impression": "string or null"
      }}
    ] or null,
    "anthropometrics": {{
      "height": {{
        "value": numeric,
        "unit": "string",
        "notes": "string or null"
      }} or null,
      "weight": {{
        "value": numeric,
        "unit": "string",
        "notes": "string or null"
      }} or null,
      "bmi": {{
        "value": numeric,
        "unit": "string",
        "notes": "string or null"
      }} or null
    }} or null,
    "diagnostic_notes": {{}} or null
  }}
}}
```

---

## Validation Checklist

Before submitting, verify:

- [ ] Labs prioritized: critical and significant abnormals extracted first
- [ ] NO routine normals unless explicitly discussed
- [ ] Lab status accurately classified (critical/abnormal_high/abnormal_low/normal)
- [ ] Clinical significance ONLY included when explicitly documented
- [ ] Baseline values ONLY extracted when explicitly stated
- [ ] Test names normalized with standard terminology
- [ ] Vital signs include abnormalities and clinically relevant values
- [ ] Physical exam findings prioritize abnormalities
- [ ] Imaging findings include negatives for rule-outs
- [ ] Anthropometrics extracted if documented
- [ ] Source sections documented for traceability
- [ ] No hallucination of clinical significance

---

<clinical_note>
{clinical_text}
</clinical_note>

Respond only with the structured JSON dictionary matching the schema, with no additional text.
"""

__all__ = ["system_prompt", "findings_prompt"]
