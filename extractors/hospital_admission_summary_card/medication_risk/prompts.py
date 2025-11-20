"""Prompts for medication risk assessment extraction."""

system_prompt = """You are a medical AI assistant analyzing medication-related risks in clinical documents.

Assess whether medications caused or contributed to hospitalization. Use evidence-based reasoning. 
Never infer or hallucinate. Extract only what's explicitly documented."""

medication_risk_prompt = '''Analyze this clinical note to assess medication-related hospitalization risk. Return ONLY valid JSON.

**Core Principle**: Assume medications are NOT the cause unless strong evidence proves otherwise. Use null hypothesis approach.

<clinical_note>
{clinical_text}
</clinical_note>

---

## Output Schema

```json
{{
  "medication_risk_assessment": {{
    "likelihood_percentage": 0-100,
    "risk_level": "high|medium|low",
    "risk_factors": [
      {{
        "factor": "description of risk factor",
        "evidence": "supporting evidence with quotes and data",
        "severity": "critical|major|moderate|minor",
        "implicated_medications": ["medication names"]
      }}
    ],
    "confidence_score": 0.0-1.0,
    "assessment_method": "ai_analysis",
    "assessed_at": "ISO 8601 timestamp"
  }}
}}
```

---

## Assessment Process

### Step 1: Determine Presentation Type

**TYPE A - Medication-Related** (Medium-High Risk):
- Medication discontinued due to adverse effect
- Symptoms consistent with drug toxicity
- Lab abnormalities indicating drug-induced organ dysfunction
- Temporal relationship: symptom onset after medication start/change
- Documented adverse drug reaction

**TYPE B - Medication Present But Unrelated** (Low Risk):
- Trauma, injury, mechanical fall with clear non-medication mechanism
- Environmental issue (power outage, transportation)
- Infection without medication-related immunosuppression
- Patient at baseline throughout encounter

**TYPE C - Medication Management Needed** (Low-Medium Risk):
- Dose adjustment needed for organ dysfunction from other causes
- Medication reconciliation or formulary substitution
- Prophylactic medication initiation

**CRITICAL**: If TYPE B or TYPE C, likelihood_percentage should typically be 0-29% (low risk) unless specific high-risk factors present.

### Step 2: Calculate Likelihood Percentage

**Likelihood of medication-related hospitalization** (0-100%):

**High Likelihood (70-100%)** - Strong evidence:
- Strong temporal relationship (symptom onset within expected timeframe after drug start/change)
- Known adverse reaction pattern matching documented presentation
- Laboratory confirmation (drug levels in toxic range, biomarkers specific to drug toxicity)
- Medication explicitly discontinued due to adverse effect
- Drug-disease contraindication with documented clinical consequence

**Medium Likelihood (30-69%)** - Moderate evidence:
- Possible temporal relationship but timing inconsistent
- Potential drug interaction without clear clinical manifestation
- Dose adjustment needed due to organ dysfunction
- Some supporting evidence but alternative explanations exist

**Low Likelihood (0-29%)** - Weak or no evidence:
- No temporal relationship
- Clear alternative explanation (trauma, environmental, infection)
- Stable chronic medications without changes
- Theoretical interactions without clinical manifestation
- Presentation clearly unrelated to medications

**Scoring Guidelines**:
- Start with base likelihood based on presentation type
- Add points for positive evidence (temporal relationship, lab confirmation, etc.)
- Subtract points for negative evidence (alternative explanations, inconsistent timing, etc.)
- Map final score to percentage range

### Step 3: Derive Risk Level

- **high**: likelihood_percentage 70-100%
- **medium**: likelihood_percentage 30-69%
- **low**: likelihood_percentage 0-29%

### Step 4: Identify Risk Factors

**CRITICAL**: If risk_level is "low", you MUST include exactly one risk factor:
```json
{{
  "factor": "No medication-related risk detected",
  "evidence": "Brief explanation of why no medication risk ",
  "severity": "minor",
  "implicated_medications": []
}}
```

**For medium/high risk, include risk factors if**:
- Medication-related problem documented
- Drug-disease interaction with clinical consequence
- Contraindicated medication administered
- Dose adjustment needed (>20% change)
- Drug interaction causing adverse effect

**For each risk factor, extract**:
- **factor**: Clear, specific description (e.g., "Metformin discontinued - potential lactic acidosis")
- **evidence**: Direct quotes with quantitative data, medication names/doses, temporal relationships
- **severity**: 
  - **critical**: Life-threatening, organ failure, severe toxicity
  - **major**: Significant risk, prompt intervention needed, contraindicated medication
  - **moderate**: Notable concern, monitoring/adjustment needed
  - **minor**: Low concern, awareness only
- **implicated_medications**: List of medication names involved (optional)

**Exclude**:
- Stable chronic medications without adverse effects
- Appropriate polypharmacy for multiple comorbidities
- Theoretical interactions without clinical manifestation
- Properly dosed medications for documented organ function

### Step 5: Set Confidence Score

- **0.90-1.00**: Strong objective evidence, clear temporal relationship, minimal missing information
- **0.75-0.89**: Good supporting evidence, probable relationship, minor information gaps
- **0.60-0.74**: Moderate evidence quality, possible relationship, significant gaps
- **0.40-0.59**: Weak evidence, uncertain relationship, major gaps
- **<0.40**: Speculative assessment, insufficient data

---

## Examples

**Example 1: High Risk - Medication-Related**
```json
{{
  "medication_risk_assessment": {{
    "likelihood_percentage": 75,
    "risk_level": "high",
    "risk_factors": [
      {{
        "factor": "Metformin discontinued during admission - potential lactic acidosis",
        "evidence": "Patient on Metformin 1000mg BID, discontinued on admission, elevated lactate 4.2 mmol/L (normal <2.0), pH 7.28",
        "severity": "critical",
        "implicated_medications": ["Metformin"]
      }},
      {{
        "factor": "Recent dose increase 7 days prior to admission",
        "evidence": "Metformin increased from 500mg BID to 1000mg BID one week before admission per HPI",
        "severity": "major",
        "implicated_medications": ["Metformin"]
      }},
      {{
        "factor": "Creatinine elevated to 2.4 mg/dL (from baseline 1.1 mg/dL)",
        "evidence": "Acute kidney injury with >100% increase in creatinine, eGFR 28 ml/min",
        "severity": "critical",
        "implicated_medications": ["Metformin"]
      }}
    ],
    "confidence_score": 0.92,
    "assessment_method": "ai_analysis",
    "assessed_at": "2025-10-18T12:00:00Z"
  }}
}}
```

**Example 2: Low Risk - Unrelated Presentation**
```json
{{
  "medication_risk_assessment": {{
    "likelihood_percentage": 5,
    "risk_level": "low",
    "risk_factors": [
      {{
        "factor": "No medication-related risk detected",
        "evidence": "Detailed explanation citing the actual presentation cause, relevant document quotes, and confirmation that medications were stable/appropriate",
        "severity": "minor",
        "implicated_medications": []
      }}
    ],
    "confidence_score": 0.95,
    "assessment_method": "ai_analysis",
    "assessed_at": "2025-10-18T12:00:00Z"
  }}
}}
```

**Example 3: Medium Risk - Dose Adjustment Needed**
```json
{{
  "medication_risk_assessment": {{
    "likelihood_percentage": 35,
    "risk_level": "medium",
    "risk_factors": [
      {{
        "factor": "Gabapentin requires renal dose adjustment",
        "evidence": "Patient with AKI (Cr 2.4), Gabapentin 600mg TID continued without adjustment, eGFR 28 ml/min",
        "severity": "moderate",
        "implicated_medications": ["Gabapentin"]
      }}
    ],
    "confidence_score": 0.80,
    "assessment_method": "ai_analysis",
    "assessed_at": "2025-10-18T12:00:00Z"
  }}
}}
```

---

## Validation Checklist

Before returning JSON, verify:
- [ ] likelihood_percentage is 0-100
- [ ] risk_level matches percentage (high: 70-100%, medium: 30-69%, low: 0-29%)
- [ ] **CRITICAL**: If risk_level is "low", risk_factors MUST contain exactly one entry with factor="No medication-related risk detected"
- [ ] Each risk factor has factor, evidence, severity
- [ ] implicated_medications is array of strings or omitted
- [ ] confidence_score is 0.0-1.0
- [ ] assessed_at is ISO 8601 format
- [ ] No over-flagging of stable chronic medications
- [ ] Environmental/trauma presentations appropriately assigned low risk

---

Return ONLY the JSON object. No explanations or additional text.
'''

__all__ = ["system_prompt", "medication_risk_prompt"]
