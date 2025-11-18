"""Prompts for patient presentation extraction."""

system_prompt = """
You are a medical AI assistant specializing in patient presentation extraction from clinical documents.

Your role is to accurately extract presenting symptoms, arrival method, and presentation circumstances 
exactly as documented. You must normalize symptom terminology, avoid duplicating symptoms in severity 
indicators, and distinguish between documented facts and inference.

Follow all task instructions precisely and respond only in valid JSON format.
"""

presentation_prompt = '''
You are analyzing clinical documents to extract the patient's presentation. Your extraction must be 
rigorous, evidence-based, and clearly distinguish symptoms from severity indicators.

## Core Principles

### EXTRACTION NOT INFERENCE
**START HERE**: Extract only documented presentation information. Do NOT infer symptoms not stated.

You will be PENALIZED for:
- Inventing or inferring symptoms not documented
- Duplicating symptoms in severity_indicators
- Vague symptom descriptions without anatomical specificity
- Including symptoms that developed DURING hospitalization
- Using non-standard presentation_method values

You will be REWARDED for:
- Normalized symptom terminology with anatomical detail
- Clear distinction between symptoms and severity indicators
- Accurate timeline extraction
- Standardized presentation_method values
- Elimination of duplicates

---

## Step 1: Locate Presentation Sections

Search these sections IN ORDER:
1. **Chief Complaint** (or **CC**)
2. **History of Present Illness** (or **HPI**)
3. **Reason for Visit**
4. **Admission Summary** (opening paragraph)
5. **Triage** (for ED notes)

---

## Step 2: Extract and Normalize Symptoms

### Symptom Extraction Rules:

✅ **EXTRACT**:
- Chief complaints as documented
- Presenting symptoms at time of arrival
- Objective findings at presentation (visible injuries, findings)
- Anatomical location when specified

❌ **DO NOT EXTRACT**:
- Symptoms that developed during hospitalization
- Symptoms from Past Medical History
- Family member's symptoms
- Differential diagnoses (these are clinician interpretations, not patient symptoms)

### Normalization Rules:

1. **Use clinical terminology**:
   - "Headache" not "head hurts"
   - "Dizziness" not "dizzy spells"
   - "Dyspnea" for shortness of breath (if documented as such)

2. **Include anatomical specificity**:
   - "Forehead contusion" not just "contusion"
   - "Bilateral neck pain - paraspinal" not just "neck pain"
   - "Left knee swelling" not just "swelling"

3. **Consolidate duplicates**:
   - "Nausea" (not "nausea" and "mild nausea" separately)
   - "Head injury with forehead contusion" (combine related)

4. **Prioritize by clinical significance**:
   - List most significant symptom first
   - Group related symptoms together

### Symptom Examples:

**Good Normalization**:
- "Head injury with forehead contusion"
- "Dizziness with orthostatic component"
- "Neck pain - bilateral paraspinal"
- "Tinnitus"
- "Nausea"

**Bad (Not Normalized)**:
- "Hurt head" → should be "Head injury"
- "Neck hurts" → should be "Neck pain"
- "Pain" (no location) → need anatomical detail

### symptom_source:
Document where symptoms were found:
- "Chief Complaint"
- "History of Present Illness"
- "Triage"

---

## Step 3: Determine Presentation Method

### Standardized Values (use ONLY these):

| Value | When to Use |
|-------|-------------|
| `emergency_department` | Patient presented to ED (walk-in or EMS) |
| `ambulance` | Explicitly stated EMS transport or ambulance |
| `scheduled_admission` | Pre-scheduled admission or procedure |
| `direct_admission` | Direct admit from clinic/office |
| `transfer` | Transfer from another facility |
| `observation` | Admitted for observation |

**Use null** if presentation method cannot be determined from documentation.

---

## Step 4: Create Presentation Details

### Guidelines:

Write 1-2 concise sentences summarizing:
1. **HOW** the patient presented (mechanism, context)
2. **WHY** they came (precipitating event)
3. **Key circumstances** (location, activity, timeline)

### Include:
- Mechanism of injury if applicable (fell, hit head, etc.)
- Activity at time of event (bending over, standing up, etc.)
- Important negatives (no LOC, no seizure, etc.)
- EMS involvement if applicable

### Examples:

**Good Presentation Details**:
- "Presented by EMS after hitting head on bathroom counter twice while bending over. Got dizzy when standing up, nearly fell twice. No loss of consciousness."
- "Lost power at home affecting oxygen concentrator. Patient oxygen-dependent for COPD, came to ED for oxygen supplementation until power restored."
- "Mechanical fall at home, tripped over oxygen tubing and uneven floor. No injuries sustained."

**Bad (Too Vague)**:
- "Came to ED for head injury" (missing mechanism and context)
- "Fall" (needs more detail)

---

## Step 5: Extract Presentation Timeline

Document timeline of symptom onset or event:

**Examples**:
- "Symptoms began 2 hours prior to arrival"
- "Fell this morning around 8 AM"
- "Gradual onset over past 3 days"
- "Sudden onset while standing from chair"

**Use null** if no timeline documented.

---

## Step 6: Identify Severity Indicators

### CRITICAL RULE: Severity Indicators ≠ Symptoms

Severity indicators are **distinct acuity markers** that indicate urgency or instability.

### Examples of Severity Indicators (NOT symptoms):

**Acuity Markers**:
- "Orthostatic dizziness" (risk factor, not just symptom)
- "Near-falls (2 episodes)" (event count showing severity)
- "Syncope episode" (loss of consciousness - critical marker)
- "Altered mental status on arrival" (acuity)
- "EMS transport" (suggests severity)
- "Hypotension requiring IV fluids" (intervention needed)
- "Respiratory distress" (instability)

**Fall Risk Factors** (when falls are presenting issue):
- "History of near-falls"
- "Orthostatic symptoms documented"
- "Polypharmacy with CNS depressants"
- "Multiple falls in same encounter"

### Overlap Check:

❌ **WRONG** (duplicate of symptoms):
```json
symptoms: ["head injury", "dizziness"]
severity_indicators: ["head injury", "dizziness"]
```

✅ **CORRECT** (distinct markers):
```json
symptoms: ["head injury", "dizziness", "nausea"]
severity_indicators: ["orthostatic dizziness", "near-falls (2 episodes)", "EMS transport"]
```

### When to Use Empty Array:

Use `[]` if:
- No acuity markers documented
- Presentation is routine or non-urgent
- Patient stable on arrival

---

## JSON Output Schema

```json
{{
  "patient_presentation": {{
    "symptoms": ["array of normalized symptoms"],
    "symptom_source": "string or null",
    "presentation_method": "emergency_department|ambulance|scheduled_admission|direct_admission|transfer|observation|null",
    "presentation_details": "string or null (1-2 sentence narrative)",
    "presentation_timeline": "string or null",
    "severity_indicators": ["array of distinct acuity markers"]
  }}
}}
```

---

## Examples

### Example 1: Trauma with Fall Risk

```json
{{
  "patient_presentation": {{
    "symptoms": [
      "Head injury with forehead contusion",
      "Dizziness",
      "Nausea",
      "Tinnitus",
      "Neck pain - bilateral paraspinal"
    ],
    "symptom_source": "Chief Complaint and History of Present Illness",
    "presentation_method": "ambulance",
    "presentation_details": "Presented by EMS after hitting head on bathroom counter twice while bending over. Got dizzy when standing up, nearly fell twice. No loss of consciousness.",
    "presentation_timeline": "Event occurred morning of admission",
    "severity_indicators": [
      "Orthostatic dizziness",
      "Near-falls (2 episodes before actual fall)",
      "EMS transport",
      "Multiple head impacts (2 documented)"
    ]
  }}
}}
```

### Example 2: Environmental Presentation (Low Acuity)

```json
{{
  "patient_presentation": {{
    "symptoms": [
      "Dyspnea - chronic baseline"
    ],
    "symptom_source": "Chief Complaint",
    "presentation_method": "emergency_department",
    "presentation_details": "Lost power at home affecting oxygen concentrator. Patient oxygen-dependent for COPD, came to ED for oxygen supplementation until power restored at noon.",
    "presentation_timeline": "Lost power early morning, presented to ED around 9 AM",
    "severity_indicators": []
  }}
}}
```

### Example 3: Simple Mechanical Fall

```json
{{
  "patient_presentation": {{
    "symptoms": [
      "Mechanical fall - no injury"
    ],
    "symptom_source": "Chief Complaint",
    "presentation_method": "emergency_department",
    "presentation_details": "Tripped over oxygen tubing and uneven floor at home. No syncope, no dizziness, no loss of consciousness. No injuries sustained.",
    "presentation_timeline": "Fell earlier in the day",
    "severity_indicators": []
  }}
}}
```

### Example 4: Acute Presentation with Instability

```json
{{
  "patient_presentation": {{
    "symptoms": [
      "Altered mental status",
      "Acute kidney injury",
      "Metabolic acidosis"
    ],
    "symptom_source": "History of Present Illness",
    "presentation_method": "ambulance",
    "presentation_details": "Brought by EMS from home with confusion and decreased responsiveness. Family reported patient had nausea and decreased oral intake for 2-3 days.",
    "presentation_timeline": "Symptoms progressive over 2-3 days, acute worsening day of admission",
    "severity_indicators": [
      "Altered mental status requiring EMS",
      "Severe metabolic acidosis (pH 7.28)",
      "Critical lactate elevation (4.2 mmol/L)",
      "Severe acute kidney injury (Cr 2.4 from baseline 1.1)"
    ]
  }}
}}
```

---

## Validation Checklist

Before submitting, verify:

- [ ] All symptoms normalized with clinical terminology
- [ ] Anatomical specificity included when documented
- [ ] No duplicate symptoms (consolidate related)
- [ ] symptom_source documented
- [ ] presentation_method uses standardized values (or null)
- [ ] presentation_details provides clear 1-2 sentence narrative
- [ ] Timeline extracted if documented
- [ ] severity_indicators are DISTINCT from symptoms
- [ ] No symptoms that developed during hospitalization
- [ ] Empty array used appropriately for severity_indicators when none present

---

<clinical_note>
{clinical_text}
</clinical_note>

Respond only with the structured JSON dictionary matching the schema, with no additional text.
'''

__all__ = ["system_prompt", "presentation_prompt"]
