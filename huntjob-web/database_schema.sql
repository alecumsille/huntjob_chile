-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create applications table
CREATE TABLE IF NOT EXISTS public.applications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    company_name TEXT NOT NULL,
    job_title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'interview_scheduled', 'rejected', 'offer'
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    resume_url TEXT,
    job_description TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS) on applications
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;

-- Create policies for applications
CREATE POLICY "Users can view their own applications" 
    ON public.applications FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own applications" 
    ON public.applications FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own applications" 
    ON public.applications FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own applications" 
    ON public.applications FOR DELETE 
    USING (auth.uid() = user_id);

-- Create interviews table
CREATE TABLE IF NOT EXISTS public.interviews (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    application_id UUID REFERENCES public.applications(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMPTZ,
    type TEXT NOT NULL, -- 'hr', 'technical', 'cultural', 'case_study'
    status TEXT NOT NULL DEFAULT 'upcoming', -- 'upcoming', 'completed', 'cancelled'
    feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS) on interviews
ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;

-- Create policies for interviews
CREATE POLICY "Users can view their own interviews" 
    ON public.interviews FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own interviews" 
    ON public.interviews FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own interviews" 
    ON public.interviews FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own interviews" 
    ON public.interviews FOR DELETE 
    USING (auth.uid() = user_id);

-- Function to automatically update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_applications_updated_at
    BEFORE UPDATE ON public.applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interviews_updated_at
    BEFORE UPDATE ON public.interviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
