"""Prompts for hospital course extraction."""

system_prompt = """
You are a medical AI assistant specializing in hospital course extraction from clinical documents.

Your role is to accurately extract the chronological progression of the patient's clinical status, 
disposition, and overall response to treatment exactly as documented. You must focus on patient 
status changes and outcomes, not repeat discrete interventions already captured in the Treatments entity.

Follow all task instructions precisely and respond only in valid JSON format.
"""

course_prompt = '''
You are analyzing clinical documents to extract the hospital course. Your extraction must focus on the 
chronological progression of the patient's condition and outcomes, distinct from discrete interventions.

## Core Principles

### EXTRACTION NOT INFERENCE
**START HERE**: Extract only documented course events and outcomes. Do NOT infer progression not stated.

You will be PENALIZED for:
- Duplicating treatments/interventions (those belong in Treatments entity)
- Free-form unstructured timeline events
- Vague event descriptions
- Unclear outcome criteria
- Inferring patient response not documented

You will be REWARDED for:
- Focused timeline of patient STATUS CHANGES and OUTCOMES
- Clear distinction from Treatments entity
- Specific, documented patient responses
- Accurate disposition classification
- Appropriate use of null for missing data

---

## CRITICAL DISTINCTION: Course vs Treatments

**COURSE Entity (this entity)**:
- Patient's clinical progression over time
- Status changes (improved, worsened, stabilized)
- Outcomes and responses to treatment
- Key milestones in the encounter
- Overall narrative of the stay

**TREATMENTS Entity (different entity)**:
- Discrete interventions (medications, procedures, therapies)
- Specific treatments provided
- Individual diagnostic tests

**AVOID**: Don't list every intervention - focus on PATIENT PROGRESSION.

---

## Step 1: Locate Course Sections

Search these sections:
1. **Hospital Course** / **Course** / **Clinical Course**
2. **Summary** (opening narrative)
3. **Assessment and Plan** (for outcomes)
4. **Discharge Summary** (narrative portions)

---

## Step 2: Extract Timeline Events

### What to Extract:

**Patient Status Changes**:
- "Patient improved with treatment"
- "Symptoms resolved"
- "Condition stabilized"
- "Developed complication X"
- "Clinical deterioration noted"

**Key Milestones**:
- "Arrived by EMS"
- "Admitted to observation"
- "Transferred to ICU"
- "Cleared for discharge"

**Outcomes**:
- "Pain controlled"
- "Creatinine normalized"
- "Patient at baseline"
- "Symptoms resolved"

### What NOT to Extract:

❌ **DO NOT extract discrete interventions** (these are in Treatments entity):
- "CT scan performed" → This is a treatment, not course progression
- "Started on antibiotics" → This is a treatment
- "IV fluids given" → This is a treatment

✅ **DO extract patient responses to interventions**:
- "Improved with IV fluids" → This is a course event (patient response)
- "Pain resolved after analgesics" → This is a course event (outcome)

### Event Format:

**event**: Description of status change or milestone
- "Patient improved with symptomatic treatment"
- "Symptoms resolved by time of discharge"
- "Arrived by EMS after fall at home"

**time**: Timing of the event
- "On arrival"
- "During ED stay"
- "Hospital Day 2"
- "By discharge"
- "2025-07-31 21:42"
- null if timing not specified

**details**: Additional context
- "Patient felt significantly better"
- "All labs normalized"
- "Ready for discharge home"
- null if no additional details

### Example Timeline:

```json
[
  {{
    "event": "Presented to ED by EMS after fall at home",
    "time": "On arrival",
    "details": "Patient with dizziness and head injury after hitting counter twice"
  }},
  {{
    "event": "Imaging completed showing no acute injury",
    "time": "During ED stay",
    "details": "CT head negative for intracranial injury"
  }},
  {{
    "event": "Symptoms improved with supportive care",
    "time": "During observation",
    "details": "Dizziness resolved, headache improved"
  }},
  {{
    "event": "Patient at baseline and ready for discharge",
    "time": "By discharge",
    "details": "All symptoms resolved, patient ambulatory without issues"
  }}
]
```

---

## Step 3: Create Narrative Summary

### Guidelines:

Write a concise 2-3 sentence summary of the overall clinical course.

**Include**:
- Reason for presentation
- Key events or findings
- Overall outcome

**Format**: Connected narrative, not bullet points.

### Example:

```
"Patient presented to ED by EMS after fall at home with head injury and dizziness. Workup including 
CT head was negative for acute injury. Patient improved with symptomatic treatment and was discharged 
home with follow-up instructions."
```

**Use null** if no narrative summary can be constructed from documentation.

---

## Step 4: Extract Disposition

### Standardized Disposition Values:

| Value | When to Use |
|-------|-------------|
| `discharged_home` | Discharged to patient's home |
| `discharged_home_with_services` | Home with home health, PT, etc. |
| `admitted_observation` | Admitted for observation |
| `admitted_inpatient` | Admitted as inpatient |
| `transferred` | Transferred to another facility |
| `left_AMA` | Left against medical advice |
| `deceased` | Patient died during encounter |

**Use null** if disposition not documented.

---

## Step 5: Extract Length of Stay

### Format:

Extract as documented:
- "3 hours"
- "Same day discharge"
- "ED observation - same day discharge"
- "2 days"
- "4 hour ED stay"

**Use null** if not documented.

---

## Step 6: Extract Patient Response

### Definition:
**Overall patient response to treatment and clinical course.**

### Examples:

- "Patient felt significantly better after symptomatic treatment"
- "Symptoms resolved completely by discharge"
- "Patient improved with IV fluids and supportive care"
- "Condition stabilized, patient at baseline"
- "Minimal improvement despite treatment"

**Use null** if patient response not explicitly documented.

---

## JSON Output Schema

```json
{{
  "hospital_course": {{
    "timeline": [
      {{
        "event": "string (description of status change or milestone)",
        "time": "string or null (timing)",
        "details": "string or null (additional context)"
      }}
    ],
    "narrative_summary": "string or null (2-3 sentence overview)",
    "disposition": "discharged_home|discharged_home_with_services|admitted_observation|admitted_inpatient|transferred|left_AMA|deceased|null",
    "length_of_stay": "string or null",
    "patient_response": "string or null"
  }}
}}
```

---

## Examples

### Example 1: ED Visit with Discharge

```json
{{
  "hospital_course": {{
    "timeline": [
      {{
        "event": "Presented to ED by EMS after fall at home",
        "time": "On arrival",
        "details": "Chief complaints: head injury, dizziness, nausea"
      }},
      {{
        "event": "Workup completed including CT head and cervical spine imaging",
        "time": "During ED stay",
        "details": "Imaging negative for acute injury"
      }},
      {{
        "event": "Symptoms improved with symptomatic treatment",
        "time": "During observation",
        "details": "Nausea resolved, headache improved, dizziness decreased"
      }},
      {{
        "event": "Patient at baseline and cleared for discharge",
        "time": "By discharge",
        "details": "Ambulatory without issues, symptoms minimal"
      }}
    ],
    "narrative_summary": "Patient presented to ED by EMS after fall at home with head injury and dizziness. Workup including CT head and cervical spine imaging was negative for acute injury. Patient improved with symptomatic treatment and was discharged home with follow-up instructions.",
    "disposition": "discharged_home",
    "length_of_stay": "ED observation - same day discharge",
    "patient_response": "Patient felt significantly better after symptomatic treatment and by time of discharge was at baseline"
  }}
}}
```

### Example 2: Simple Environmental Presentation

```json
{{
  "hospital_course": {{
    "timeline": [
      {{
        "event": "Presented to ED after power outage at home",
        "time": "On arrival",
        "details": "Oxygen-dependent patient unable to use home concentrator"
      }},
      {{
        "event": "Placed on supplemental oxygen with improvement",
        "time": "Immediately upon arrival",
        "details": "SpO2 improved to baseline, patient comfortable"
      }},
      {{
        "event": "Remained in ED for observation until power restored",
        "time": "Throughout stay",
        "details": "Patient at clinical baseline entire time"
      }},
      {{
        "event": "Power restored at home, patient discharged",
        "time": "By noon",
        "details": "Patient able to return home with functioning oxygen concentrator"
      }}
    ],
    "narrative_summary": "Patient presented to ED after power outage at home affecting oxygen concentrator. Patient oxygen-dependent for COPD and required temporary oxygen supplementation. Remained in ED for observation until power restored at home, then discharged.",
    "disposition": "discharged_home",
    "length_of_stay": "4 hours",
    "patient_response": "Patient at baseline throughout encounter, no acute issues"
  }}
}}
```

### Example 3: Inpatient Admission

```json
{{
  "hospital_course": {{
    "timeline": [
      {{
        "event": "Admitted with acute kidney injury and metabolic acidosis",
        "time": "On admission",
        "details": "Creatinine 2.4 (baseline 1.1), lactate 4.2, pH 7.28"
      }},
      {{
        "event": "Initiated IV fluid resuscitation and supportive care",
        "time": "Hospital Day 1",
        "details": "Aggressive hydration, medication reconciliation completed"
      }},
      {{
        "event": "Clinical improvement with treatment",
        "time": "Hospital Day 2",
        "details": "Creatinine improving, lactate normalizing, mental status clearing"
      }},
      {{
        "event": "Labs normalized, patient at baseline",
        "time": "Hospital Day 3",
        "details": "Creatinine 1.3 (near baseline), lactate normal, pH normalized"
      }},
      {{
        "event": "Cleared for discharge",
        "time": "Hospital Day 3",
        "details": "Patient stable, tolerating oral intake, ambulating independently"
      }}
    ],
    "narrative_summary": "Patient admitted with acute kidney injury and lactic acidosis, likely secondary to metformin in setting of declining renal function. Improved with IV fluid resuscitation and supportive care. Labs normalized by Hospital Day 3 and patient was discharged home with close follow-up.",
    "disposition": "discharged_home_with_services",
    "length_of_stay": "3 days",
    "patient_response": "Excellent response to treatment with complete resolution of AKI and acidosis"
  }}
}}
```

---

## Validation Checklist

Before submitting, verify:

- [ ] Timeline events focus on patient STATUS CHANGES, not discrete interventions
- [ ] No duplication with Treatments entity (interventions extracted there)
- [ ] Events have specific descriptions, not vague statements
- [ ] Timing provided for events when documented
- [ ] Narrative summary is 2-3 connected sentences (not bullet points)
- [ ] Disposition uses standardized values
- [ ] Length of stay extracted as documented
- [ ] Patient response reflects documented outcomes
- [ ] Empty array used for timeline if no events documented
- [ ] Null used appropriately for optional fields

---

<clinical_note>
{clinical_text}
</clinical_note>

Respond only with the structured JSON dictionary matching the schema, with no additional text.
'''

__all__ = ["system_prompt", "course_prompt"]
