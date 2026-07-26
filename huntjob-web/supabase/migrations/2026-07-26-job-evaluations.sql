-- supabase/migrations/2026-07-26-job-evaluations.sql
CREATE TABLE IF NOT EXISTS job_evaluations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  job_url TEXT NOT NULL,
  company_name TEXT NOT NULL,
  job_title TEXT NOT NULL,
  jd_raw TEXT NOT NULL,
  overall_score NUMERIC(2,1) NOT NULL CHECK (overall_score >= 1.0 AND overall_score <= 5.0),
  blocks JSONB NOT NULL,
  is_suspicious BOOLEAN NOT NULL DEFAULT false,
  suspicious_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE applications ADD COLUMN IF NOT EXISTS evaluation_id UUID REFERENCES job_evaluations(id);

ALTER TABLE job_evaluations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own evaluations" ON job_evaluations;
CREATE POLICY "Users can view their own evaluations" ON job_evaluations
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own evaluations" ON job_evaluations;
CREATE POLICY "Users can insert their own evaluations" ON job_evaluations
  FOR INSERT WITH CHECK (auth.uid() = user_id);
