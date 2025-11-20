"""Prompts for patient presentation extraction."""

system_prompt = """You are a medical data extraction specialist. Extract patient presentation information from clinical documents.

Focus on how and why the patient arrived. Return valid JSON only."""

presentation_prompt = '''Extract patient presentation from this clinical note.

<clinical_note>
{clinical_text}
</clinical_note>

---

## YOUR TASK

Extract presentation in 3 steps:
1. Find patient IDs
2. Extract presenting symptoms and context
3. Format as JSON

---

## STEP 1: FIND IDs

**patient_id:**
- Look for "MRN:" in document header
- Extract the number after it (8-10 digits)
- Example: "MRN: 10838402" → "10838402"
- **DO NOT USE**: RRD numbers (like "RRD 5552312523751")

**hospitalization_id:**
- Look for "Account Number:" in document header
- Extract the number after it (~10 digits)
- Example: "Account Number: 4002138129" → "4002138129"

---

## STEP 2: EXTRACT PRESENTATION

### A. Find Symptoms

**Where to look:**
- Chief Complaint section
- History of Present Illness section
- Reason for Visit

**What to extract:**
- Symptoms patient had when they arrived
- Injuries or findings at presentation
- Main complaint or reason for visit

**Examples:**
- "Smoke inhalation"
- "Shortness of breath"
- "Chest pain"
- "Head injury"
- "Dizziness"
- "Nausea"

**Normalize abbreviations:**
- SOB → "Shortness of breath"
- LOC → "Loss of consciousness"
- N/V → "Nausea and vomiting"

**Keep it simple:** Extract as documented, don't over-interpret.

---

### B. Document Where Found

**symptom_source:**
- Record which section you found symptoms in
- Examples: "Chief Complaint", "History of Present Illness", "Chief Complaint and History of Present Illness"

---

### C. Determine Arrival Method

**presentation_method** (pick one):
- "ambulance" = arrived by EMS/ambulance
- "emergency_department" = walked in or brought by family
- "transfer" = transferred from another hospital
- "scheduled_admission" = planned admission
- "direct_admission" = admitted directly from clinic
- null = not documented

**Most common:**
- If says "EMS", "ambulance", "paramedics" → "ambulance"
- If says "walked in", "brought by family", "self-presented" → "emergency_department"

---

### D. Write Presentation Summary

**presentation_details:**
Write 1-3 sentences answering:
- How did patient arrive? (EMS? Walk-in?)
- Why did they come? (What happened?)
- What was the situation? (Context, location, activity)

**Good examples:**
- "Presented by EMS after plastic spice rack caught fire on stove, causing smoke inhalation. Patient reports shortness of breath."
- "Arrived by ambulance after fall at home. Hit head on counter, had dizziness."
- "Walked into ED with chest pain that started 2 hours ago while at rest."

**Keep it factual:** Just describe what happened, no interpretation.

---

### E. Extract Timeline (if available)

**presentation_timeline:**
- When did symptoms start?
- When did event occur?
- How long between event and arrival?

**Examples:**
- "Symptoms started 2 hours before arrival"
- "Event occurred this morning"
- "Arrived 2025-08-29 21:30 EDT"
- "Seen earlier same day for chest pain"

**Use null if timing not documented.**

---

### F. Note Severity Indicators

**severity_indicators:**
List factors showing this was urgent or serious:

**Include things like:**
- "EMS transport required"
- "Respiratory distress"
- "Altered mental status"
- "Multiple falls"
- "Oxygen-dependent at baseline"
- "Second ED visit same day"
- Physical exam findings: "Mild wheezing", "Hypotension"

**Don't just repeat symptoms** - add context that shows severity.

**Empty array [] is fine** if presentation was routine/non-urgent.

---

## STEP 3: OUTPUT JSON
```json
{{
  "patient_presentation": {{
    "symptoms": ["array of symptoms"],
    "symptom_source": "where found",
    "presentation_method": "ambulance|emergency_department|transfer|scheduled_admission|direct_admission|null",
    "presentation_details": "1-3 sentence summary",
    "presentation_timeline": "timing info or null",
    "severity_indicators": ["factors showing severity"]
  }},
  "patient_id": "MRN string",
  "hospitalization_id": "Account Number string"
}}
```

---

## EXAMPLES

### Example 1: Chemical exposure

**Input snippet:**
```
MRN: 10838402
Account Number: 4002138129
Chief Complaint: Patient arrives by EMS after plastic spice rack caught on fire
History: 85-year-old with COPD, reports smoke inhalation, shortness of breath
Vitals: SpO2 100%, mild bilateral wheezing
Earlier today: seen for chest pain, COPD exacerbation, started on Decadron
```

**Output:**
```json
{{
  "patient_presentation": {{
    "symptoms": [
      "Smoke inhalation",
      "Shortness of breath"
    ],
    "symptom_source": "Chief Complaint and History of Present Illness",
    "presentation_method": "ambulance",
    "presentation_details": "Presented by EMS after plastic spice rack caught fire on stove, leading to smoke inhalation. Patient with COPD reports shortness of breath and respiratory irritation. Seen earlier same day for COPD exacerbation.",
    "presentation_timeline": "Arrived 2025-08-29 21:30 EDT. Earlier same-day visit for chest pain and COPD exacerbation.",
    "severity_indicators": [
      "EMS transport required",
      "Chemical fume exposure",
      "COPD exacerbation",
      "Mild bilateral wheezing on exam",
      "Oxygen-dependent at baseline (2-3L)",
      "Second ED visit same day"
    ]
  }},
  "patient_id": "10838402",
  "hospitalization_id": "4002138129"
}}
```

### Example 2: Simple presentation

**Input snippet:**
```
MRN: 12345678
Account Number: 9876543210
Chief Complaint: Chest pain
History: 55-year-old male with chest pain started 2 hours ago, came by car
```

**Output:**
```json
{{
  "patient_presentation": {{
    "symptoms": [
      "Chest pain"
    ],
    "symptom_source": "Chief Complaint",
    "presentation_method": "emergency_department",
    "presentation_details": "55-year-old male presented with chest pain that started 2 hours prior to arrival. Arrived by private vehicle.",
    "presentation_timeline": "Symptoms started 2 hours before arrival",
    "severity_indicators": []
  }},
  "patient_id": "12345678",
  "hospitalization_id": "9876543210"
}}
```

### Example 3: Trauma

**Input snippet:**
```
MRN: 11223344
Account Number: 5566778899
Chief Complaint: Fall with head injury
EMS transported: Patient fell at home, hit head on counter
HPI: Tripped over rug, struck forehead, no LOC
```

**Output:**
```json
{{
  "patient_presentation": {{
    "symptoms": [
      "Head injury",
      "Forehead trauma"
    ],
    "symptom_source": "Chief Complaint and History of Present Illness",
    "presentation_method": "ambulance",
    "presentation_details": "Patient fell at home after tripping on rug, struck forehead on counter. No loss of consciousness. Transported by EMS.",
    "presentation_timeline": "Fell earlier today",
    "severity_indicators": [
      "EMS transport",
      "Head trauma requiring evaluation"
    ]
  }},
  "patient_id": "11223344",
  "hospitalization_id": "5566778899"
}}
```

---

## KEY RULES

1. **IDs first** - Always extract patient_id (MRN) and hospitalization_id (Account Number)
2. **Don't use RRD** - If you see "RRD 5552312523751", that's NOT the MRN
3. **Symptoms = what patient had on arrival** - Not what developed later
4. **Keep symptoms simple** - Extract as documented
5. **Presentation details = tell the story** - How/why they came
6. **Severity indicators ≠ symptoms** - Add context, don't just repeat symptoms
7. **Null is OK** - Use null for timeline or presentation_method if not documented

Return only JSON. No other text.
'''

__all__ = ["system_prompt", "presentation_prompt"]
