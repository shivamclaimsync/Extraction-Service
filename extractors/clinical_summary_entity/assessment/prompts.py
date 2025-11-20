"""Prompts for clinical assessment extraction."""

system_prompt = """You are a medical AI assistant extracting clinical assessments from medical documents.

Extract only documented information. Never infer or hallucinate. Return valid JSON only."""

assessment_prompt = '''Extract clinical assessment from this note. Return ONLY valid JSON.

**Core Principle**: Extract only explicitly documented information. Do NOT infer, assume, or invent diagnoses, reasoning, or relationships.

<clinical_note>
{clinical_text}
</clinical_note>

---

## Output Schema

```json
{{
  "clinical_assessment": {{
    "primary_diagnosis": "string",
    "primary_diagnosis_source": "string",
    "secondary_diagnoses": [
      {{
        "diagnosis": "string",
        "source": "string",
        "relationship": "string"
      }}
    ],
    "clinical_reasoning": ["array of reasoning statements"],
    "medication_relationship": {{
      "implicated_medications": ["medication names"],
      "mechanism": "how medications contributed",
      "evidence": "Section: \"direct quote\"",
      "confidence": "definite|probable|possible"
    }} or null,
    "cause_determination": {{
      "cause": "precipitating cause",
      "supporting_evidence": ["evidence list"],
      "evidence_source": "section name",
      "confidence": "definite|probable|possible|uncertain"
    }} or null,
    "fall_risk_assessment": {{
      "risk_level": "low|moderate|high",
      "contributing_factors": ["documented factors"]
    }} or null
  }},
  "patient_id": "MRN from document",
  "hospitalization_id": "account/encounter number"
}}
```

---

## Extraction Rules

### 1. Primary Diagnosis

**Find in** (priority order):
- This Visit Problems (first listed)
- Discharge Diagnosis (first listed)
- Assessment/Plan (main diagnosis)
- Medical Decision Making (ED visits)

**Extract**:
- Verbatim text
- Source section name

---

### 2. Secondary Diagnoses

**Include diagnoses from**:
- This Visit Problems (beyond #1)
- Discharge Diagnosis (beyond #1)
- Assessment/Plan with active management
- Medical Decision Making → "Comorbidities" subsection
- Explicitly mentioned as relevant to current encounter

**For EACH secondary diagnosis extract**:
- `diagnosis`: Verbatim text
- `source`: Section name where found
- `relationship`: "pre-existing condition", "contributing factor", "complication of", "acute exacerbation", "concurrent acute condition"

**Exclude**:
- Past Medical History ONLY (not mentioned elsewhere)
- Inactive/resolved conditions
- Entire PMH list

**KEY RULE**: If diagnosis appears in "Comorbidities" within Medical Decision Making → INCLUDE IT

---

### 3. Clinical Reasoning

**Extract documented statements about**:
- Patient presentation and history
- Physical exam key findings
- Diagnostic test results and interpretation
- Treatment response
- Clinical course and disposition
- Mechanism or pathophysiology discussed

**Format**: Array of complete sentences from the note

**Include**:
- Age, gender, key comorbidities relevant to current visit
- Presenting symptoms and mechanism
- Relevant vital signs and exam findings
- Diagnostic results (imaging, labs)
- Treatment given and response
- Disposition and follow-up plan

**Aim for 5-10 comprehensive reasoning points covering the full clinical picture**

---

### 4. Medication Relationship

**ONLY populate if ALL criteria met**:
1. Clinician explicitly links medications to presentation
2. Mechanism described (how medication contributed)
3. Direct quote available as evidence

**Populate when note states**:
- "Medication X contributed to..."
- "Drug-induced..."
- "Adverse effect of..."
- "Medication discontinued due to..."
- Explicit mechanism linking drugs to presentation

**Do NOT populate when**:
- Medications listed but not implicated
- Presentation clearly environmental/trauma with no drug involvement
- Stable chronic therapy without issues
- No explicit connection stated

**Confidence levels**:
- `definite`: Lab confirmation, explicit causation documented, medication stopped
- `probable`: Strong clinical suspicion with mechanism stated
- `possible`: Mentioned as possibility but uncertain

**Set to null if no medication involvement documented**

---

### 5. Cause Determination

**Populate when clinician explicitly identifies cause**

**Examples**:
- "Chemical irritant from burning plastic"
- "Mechanical fall due to tripping"
- "Orthostatic hypotension leading to fall"
- "Power outage affecting oxygen supply"

**Extract**:
- `cause`: Clinician's stated cause (verbatim or close paraphrase)
- `supporting_evidence`: List of supporting facts from note (3-6 points)
- `evidence_source`: Section name(s) where discussed
- `confidence`:
  - `definite`: Objective evidence confirms cause
  - `probable`: Strong clinical suspicion
  - `possible`: Plausible but alternatives exist
  - `uncertain`: Multiple possibilities, unclear

**Set to null if cause not identified or unclear**

---

### 6. Fall Risk Assessment

**ONLY populate if**:
- Falls mentioned in note, OR
- Near-falls documented, OR
- Fall risk explicitly assessed

**Risk levels**:
- `low`: 0-1 risk factors, no falls
- `moderate`: 2-3 risk factors, OR 1 fall, OR near-fall episodes
- `high`: 4+ risk factors, OR recurrent falls (2+), OR serious injury from fall

**Contributing factors** (document-based only):
- Specific medications (name them: "Opioids", "Benzodiazepines", "Diuretics")
- Physical findings ("Orthostatic hypotension", "Mobility impairment")
- Clinical conditions ("Baseline hypoxemia", "Morbid obesity", "Dementia")
- History ("Previous falls", "Near-fall episodes")
- Polypharmacy (if >10-15 medications)
- Environmental hazards (if documented)

**Set to null if falls not discussed**

---

### 7. Patient/Hospitalization IDs

**Extract**:
- `patient_id`: MRN (Medical Record Number)
- `hospitalization_id`: Account Number or Encounter Number

**Common locations**:
- Header section with patient demographics
- "Account Number:", "MRN:", "Visit Number:"

---

## Examples

### Example 1: Chemical Exposure (ED Visit)
```json
{{
  "clinical_assessment": {{
    "primary_diagnosis": "Respiratory condition due to chemical fumes",
    "primary_diagnosis_source": "This Visit Problems; Assessment/Plan",
    "secondary_diagnoses": [
      {{
        "diagnosis": "COPD",
        "source": "Medical Decision Making (Comorbidities)",
        "relationship": "pre-existing condition"
      }},
      {{
        "diagnosis": "Exacerbation of COPD",
        "source": "History of Present Illness",
        "relationship": "acute exacerbation"
      }},
      {{
        "diagnosis": "Chronic hypoxemic respiratory failure",
        "source": "Past Medical History; Medical Decision Making",
        "relationship": "pre-existing condition"
      }}
    ],
    "clinical_reasoning": [
      "85-year-old female with severe baseline respiratory disease (COPD, chronic hypoxemic respiratory failure, idiopathic pulmonary fibrosis, oxygen-dependent at 2-3L continuously)",
      "Seen earlier same day in ER for chest pain, diagnosed with COPD exacerbation, started on Decadron",
      "Current presentation: Chemical fume exposure from melting plastic spice rack on stove, accidentally turned on burner",
      "Reports smoke inhalation and shortness of breath",
      "Vital signs stable: T 36.8°C, HR 93, RR 16, BP 136/41, SpO2 100%",
      "Physical exam: Mild bilateral wheezing at bases, no accessory muscle use, speaking in full sentences, no facial burns or soot in oropharynx",
      "Chest X-ray: No acute cardiopulmonary process",
      "Treatment: DuoNeb nebulizer with good response, breathing improved",
      "Clinical course: Respiratory status improved after 1.5 hours observation",
      "Disposition: Discharged home stable with son, follow-up with PCP within 24-48 hours"
    ],
    "medication_relationship": null,
    "cause_determination": {{
      "cause": "Chemical irritant from burning/melting plastic that exacerbated her pre-existing COPD",
      "supporting_evidence": [
        "Patient accidentally turned on stove burner causing plastic spice rack to melt",
        "Exposed to smoke and fumes from burning plastic",
        "Presenting symptoms of respiratory irritation and shortness of breath consistent with chemical exposure",
        "Physical exam showed mild wheezing consistent with irritant exposure",
        "No evidence of thermal burns or severe smoke inhalation",
        "Improved with bronchodilator therapy (DuoNeb)"
      ],
      "evidence_source": "Chief Complaint; History of Present Illness; Medical Decision Making",
      "confidence": "definite"
    }},
    "fall_risk_assessment": null
  }},
  "patient_id": "10838402",
  "hospitalization_id": "4002138129"
}}
```

### Example 2: Fall with Medication Involvement
```json
{{
  "clinical_assessment": {{
    "primary_diagnosis": "Head injury from mechanical fall",
    "primary_diagnosis_source": "This Visit Problems; Assessment/Plan",
    "secondary_diagnoses": [
      {{
        "diagnosis": "Orthostatic hypotension",
        "source": "Assessment/Plan",
        "relationship": "contributing factor"
      }},
      {{
        "diagnosis": "Polypharmacy",
        "source": "Medical Decision Making",
        "relationship": "contributing factor"
      }}
    ],
    "clinical_reasoning": [
      "72-year-old male with multiple comorbidities presenting after fall at home",
      "Patient reports dizziness when standing up from chair, then fell forward",
      "Taking multiple CNS-active medications including opioids and benzodiazepines",
      "Vital signs: BP lying 145/82, standing BP not documented",
      "Physical exam: Forehead contusion 3cm, no loss of consciousness",
      "CT head: No acute intracranial process",
      "Clinician notes high-risk medication profile for orthostatic hypotension"
    ],
    "medication_relationship": {{
      "implicated_medications": ["Morphine ER 30mg BID", "Lorazepam 0.5mg PRN", "Torsemide 60mg daily"],
      "mechanism": "CNS depressants and diuretic contributing to orthostatic hypotension and fall risk",
      "evidence": "Medical Decision Making: \"Patient on high-risk medication combination including opioid, benzodiazepine, and high-dose diuretic which likely contributed to orthostatic symptoms and fall\"",
      "confidence": "probable"
    }},
    "cause_determination": {{
      "cause": "Orthostatic hypotension precipitating mechanical fall",
      "supporting_evidence": [
        "Patient reports dizziness when standing immediately before fall",
        "High-risk medications for orthostatic hypotension",
        "No syncope or seizure activity",
        "Clear temporal relationship between standing and fall"
      ],
      "evidence_source": "History of Present Illness; Medical Decision Making",
      "confidence": "probable"
    }},
    "fall_risk_assessment": {{
      "risk_level": "high",
      "contributing_factors": [
        "Polypharmacy (>15 medications)",
        "Opioid therapy (Morphine ER)",
        "Benzodiazepine use (Lorazepam)",
        "High-dose diuretic (Torsemide 60mg)",
        "Documented orthostatic symptoms",
        "History of dizziness with position changes",
        "Age >70 years"
      ]
    }}
  }},
  "patient_id": "10838402",
  "hospitalization_id": "4002138129"
}}
```

### Example 3: Simple Trauma - No Medication Issues
```json
{{
  "clinical_assessment": {{
    "primary_diagnosis": "Ankle sprain",
    "primary_diagnosis_source": "Assessment/Plan",
    "secondary_diagnoses": [],
    "clinical_reasoning": [
      "28-year-old healthy male twisted ankle playing basketball",
      "Immediate pain and swelling, able to bear weight with difficulty",
      "Physical exam: Lateral ankle tenderness, mild swelling, intact neurovascular status",
      "X-ray: No fracture identified",
      "Treatment: Ice, elevation, NSAID, ankle brace",
      "Disposition: Discharged home with crutches, follow-up as needed"
    ],
    "medication_relationship": null,
    "cause_determination": {{
      "cause": "Sports injury - ankle inversion while playing basketball",
      "supporting_evidence": [
        "Clear mechanism: landed awkwardly after jump",
        "Immediate onset of pain and swelling",
        "No prior ankle problems",
        "Injury consistent with mechanism"
      ],
      "evidence_source": "History of Present Illness",
      "confidence": "definite"
    }},
    "fall_risk_assessment": null
  }},
  "patient_id": "12345678",
  "hospitalization_id": "9876543210"
}}
```

---

## Critical Reminders

1. ✅ **Secondary diagnoses**: Include ALL from This Visit Problems, Discharge Diagnosis list, Assessment/Plan, AND Medical Decision Making "Comorbidities"
2. ✅ **Clinical reasoning**: Aim for 5-10 comprehensive points covering full clinical picture
3. ✅ **Medication relationship**: null unless explicitly documented by clinician
4. ✅ **Cause determination**: Extract clinician's stated cause with supporting evidence
5. ✅ **Fall risk**: null if falls not discussed; assess properly if mentioned
6. ✅ **Evidence**: Use direct quotes where possible
7. ❌ **Never infer**: Don't add information not in the document
8. ❌ **Don't dump PMH**: Only include diagnoses relevant to current encounter

---

Return ONLY the JSON. No explanations or additional text.
'''

__all__ = ["system_prompt", "assessment_prompt"]
