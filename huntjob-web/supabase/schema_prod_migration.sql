-- =====================================================
-- HuntJob — Migración de producción (2026-07-25)
-- =====================================================
-- Versión corregida de supabase/schema.sql para correr contra una
-- base de datos que YA tiene una tabla `applications` con forma vieja
-- (resume_url/job_description en vez de job_url/adapted_cv, sin `profiles`
-- todavía). Diferencias respecto al schema.sql original:
--   1. Agrega ALTER TABLE ... ADD COLUMN IF NOT EXISTS para job_url y
--      adapted_cv en applications (CREATE TABLE IF NOT EXISTS no las
--      hubiera agregado porque la tabla ya existe).
--   2. Todas las políticas usan DROP POLICY IF EXISTS antes de CREATE
--      POLICY (Postgres no soporta CREATE POLICY IF NOT EXISTS), para que
--      esto se pueda correr más de una vez sin error si ya hay políticas
--      con el mismo nombre.
--   3. Backfillea una fila en profiles para cada usuario que ya existía
--      en auth.users antes de que este trigger existiera (si no, el
--      primer intento de guardar CV/postular de un usuario viejo falla
--      por la FK a profiles).
-- Seguro de correr más de una vez (todo es idempotente).
-- =====================================================

-- 1. PROFILES — Perfil extendido del usuario
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT,
  phone TEXT,
  linkedin_url TEXT,
  location TEXT,
  desired_role TEXT,
  salary_expectation TEXT,
  work_modality TEXT,
  professional_summary TEXT,
  plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
  ai_credits_used INTEGER NOT NULL DEFAULT 0,
  ai_credits_limit INTEGER NOT NULL DEFAULT 10,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. APPLICATIONS — ya existe en prod con forma vieja; solo agregamos
--    las columnas que /api/apply/route.ts necesita y que faltan.
CREATE TABLE IF NOT EXISTS applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  company_name TEXT NOT NULL,
  job_title TEXT NOT NULL,
  job_url TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'interview_scheduled', 'rejected', 'offer', 'withdrawn')),
  notes TEXT,
  adapted_cv JSONB,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE applications ADD COLUMN IF NOT EXISTS job_url TEXT;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS adapted_cv JSONB;

-- 3. RESUMES — CVs generados/guardados
CREATE TABLE IF NOT EXISTS resumes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL DEFAULT 'Mi CV',
  cv_data JSONB NOT NULL,
  target_company TEXT,
  target_role TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. INTERVIEW_SESSIONS — Historial de entrevistas simuladas
CREATE TABLE IF NOT EXISTS interview_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  company TEXT,
  role TEXT,
  interview_type TEXT CHECK (interview_type IN ('technical', 'hr', 'general')),
  messages JSONB NOT NULL DEFAULT '[]'::jsonb,
  score INTEGER,
  feedback TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at TIMESTAMPTZ
);

-- 5. PAYMENTS — Historial de pagos (Flow.cl)
CREATE TABLE IF NOT EXISTS payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  flow_order_id TEXT,
  flow_payment_status TEXT,
  amount INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'CLP',
  plan TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_user_id ON interview_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_plan ON profiles(plan);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Profiles: usuarios solo ven su propio perfil
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
CREATE POLICY "Users can insert own profile" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- Applications: usuarios solo ven sus postulaciones
DROP POLICY IF EXISTS "Users can view own applications" ON applications;
CREATE POLICY "Users can view own applications" ON applications
  FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can insert own applications" ON applications;
CREATE POLICY "Users can insert own applications" ON applications
  FOR INSERT WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can update own applications" ON applications;
CREATE POLICY "Users can update own applications" ON applications
  FOR UPDATE USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can delete own applications" ON applications;
CREATE POLICY "Users can delete own applications" ON applications
  FOR DELETE USING (auth.uid() = user_id);

-- Resumes: usuarios solo ven sus CVs
DROP POLICY IF EXISTS "Users can view own resumes" ON resumes;
CREATE POLICY "Users can view own resumes" ON resumes
  FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can insert own resumes" ON resumes;
CREATE POLICY "Users can insert own resumes" ON resumes
  FOR INSERT WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can update own resumes" ON resumes;
CREATE POLICY "Users can update own resumes" ON resumes
  FOR UPDATE USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can delete own resumes" ON resumes;
CREATE POLICY "Users can delete own resumes" ON resumes
  FOR DELETE USING (auth.uid() = user_id);

-- Interview Sessions: usuarios solo ven sus entrevistas
DROP POLICY IF EXISTS "Users can view own interviews" ON interview_sessions;
CREATE POLICY "Users can view own interviews" ON interview_sessions
  FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can insert own interviews" ON interview_sessions;
CREATE POLICY "Users can insert own interviews" ON interview_sessions
  FOR INSERT WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can update own interviews" ON interview_sessions;
CREATE POLICY "Users can update own interviews" ON interview_sessions
  FOR UPDATE USING (auth.uid() = user_id);

-- Payments: usuarios solo ven sus pagos
DROP POLICY IF EXISTS "Users can view own payments" ON payments;
CREATE POLICY "Users can view own payments" ON payments
  FOR SELECT USING (auth.uid() = user_id);

-- =====================================================
-- TRIGGER: auto-create profile on signup
-- =====================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =====================================================
-- TRIGGER: auto-update updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_profiles_updated_at ON profiles;
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

DROP TRIGGER IF EXISTS update_applications_updated_at ON applications;
CREATE TRIGGER update_applications_updated_at
  BEFORE UPDATE ON applications
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- =====================================================
-- BACKFILL: crea profiles para usuarios que ya existían
-- antes de este trigger (si no, su primer guardado de CV
-- o postulación falla por la foreign key a profiles).
-- =====================================================
INSERT INTO public.profiles (id, email, full_name)
SELECT
  u.id,
  u.email,
  COALESCE(u.raw_user_meta_data->>'full_name', split_part(u.email, '@', 1))
FROM auth.users u
LEFT JOIN public.profiles p ON p.id = u.id
WHERE p.id IS NULL
ON CONFLICT (id) DO NOTHING;
