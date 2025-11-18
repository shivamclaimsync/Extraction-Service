-- Database schema for extraction service
-- PostgreSQL 14+

-- Create extension for UUID generation (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Hospital summaries table
CREATE TABLE IF NOT EXISTS public.hospital_summaries
(
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    
    -- Identifiers
    hospitalization_id text COLLATE pg_catalog."default",
    patient_id text COLLATE pg_catalog."default" NOT NULL,
    
    -- JSONB columns (store Pydantic models)
    -- These columns store the complete nested structure from FacilityData, TimingData,
    -- DiagnosisData, and RiskAssessment Pydantic models
    facility jsonb NOT NULL,
    timing jsonb NOT NULL,
    diagnosis jsonb NOT NULL,
    medication_risk_assessment jsonb NOT NULL,
    
    -- Computed/metadata fields
    length_of_stay_days integer NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    
    -- Primary key
    CONSTRAINT hospital_summaries_pkey PRIMARY KEY (id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS ix_hospital_summaries_patient_id 
    ON public.hospital_summaries USING btree (patient_id COLLATE pg_catalog."default");

CREATE INDEX IF NOT EXISTS ix_hospital_summaries_hospitalization_id 
    ON public.hospital_summaries USING btree (hospitalization_id COLLATE pg_catalog."default");

CREATE INDEX IF NOT EXISTS ix_hospital_summaries_created_at 
    ON public.hospital_summaries USING btree (created_at DESC);

-- Optional: GIN index for JSONB columns to enable efficient JSON queries
CREATE INDEX IF NOT EXISTS ix_hospital_summaries_facility_gin 
    ON public.hospital_summaries USING gin (facility);

CREATE INDEX IF NOT EXISTS ix_hospital_summaries_diagnosis_gin 
    ON public.hospital_summaries USING gin (diagnosis);

-- Comments documenting JSONB structure
COMMENT ON TABLE public.hospital_summaries IS 'Hospital admission summaries extracted from clinical notes';

COMMENT ON COLUMN public.hospital_summaries.facility IS 
'Facility information (JSONB):
{
  "facility_name": str,
  "facility_id": str | null,
  "facility_type": "acute_care" | "psychiatric" | "rehabilitation" | "ltac",
  "address": {
    "street": str | null,
    "city": str,
    "state": str,
    "zip": str | null
  }
}';

COMMENT ON COLUMN public.hospital_summaries.timing IS 
'Admission and discharge timing (JSONB):
{
  "admission_date": str (ISO 8601),
  "admission_time": str | null (HH:MM),
  "discharge_date": str (ISO 8601),
  "discharge_time": str | null (HH:MM),
  "admission_source": "emergency_dept" | "direct_admission" | "transfer" | "scheduled" | null,
  "discharge_disposition": "home" | "snf" | "home_health" | "rehab" | "transfer" | "expired" | null
}';

COMMENT ON COLUMN public.hospital_summaries.diagnosis IS 
'Primary and secondary diagnoses (JSONB):
{
  "primary_diagnosis": str,
  "primary_diagnosis_icd10": str | null,
  "primary_diagnosis_evidence": str,
  "diagnosis_category": str,
  "secondary_diagnoses": [
    {
      "diagnosis": str,
      "icd10_code": str | null,
      "evidence": str,
      "relationship_to_primary": str | null
    }
  ]
}';

COMMENT ON COLUMN public.hospital_summaries.medication_risk_assessment IS 
'Medication risk assessment (JSONB):
{
  "metadata": {...},
  "clinical_context": {...},
  "risk_scoring": {...},
  "likelihood_percentage": {
    "percentage": int (0-100),
    "evidence": str,
    "calculation_method": str
  },
  "risk_level": "high" | "medium" | "low",
  "risk_factors": [...],
  "alternative_explanations": [...],
  "negative_findings": [...],
  "confidence_score": float (0.0-1.0),
  "confidence_rationale": str,
  "assessment_method": "ai_analysis" | "pharmacist_determination" | "combined",
  "assessed_at": str (ISO 8601)
}';

-- Example queries

-- Get all records for a patient
-- SELECT * FROM hospital_summaries WHERE patient_id = 'PAT-123' ORDER BY created_at DESC;

-- Get by hospitalization_id
-- SELECT * FROM hospital_summaries WHERE hospitalization_id = 'HOSP-456';

-- Query JSONB fields (requires GIN index for performance)
-- SELECT * FROM hospital_summaries WHERE facility->>'facility_name' = 'Memorial Hospital';
-- SELECT * FROM hospital_summaries WHERE diagnosis->>'primary_diagnosis' ILIKE '%myocardial%';
-- SELECT * FROM hospital_summaries WHERE (medication_risk_assessment->>'risk_level') = 'high';

