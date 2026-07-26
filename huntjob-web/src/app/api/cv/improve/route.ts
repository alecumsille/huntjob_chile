import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/ssr';
import { improveCv } from '@/lib/ai/cv-improver';
import { CVData } from '@/lib/document/docx-generator';
import { auditLog } from '@/lib/security/audit-log';

export async function POST(req: Request) {
  try {
    const cookieStore = await cookies();
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://dummy.supabase.co',
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'dummy_key',
      {
        cookies: {
          getAll() {
            return cookieStore.getAll();
          },
        },
      }
    );

    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      auditLog({ action: 'auth.unauthorized', path: '/api/cv/improve', ip: req.headers.get('x-forwarded-for') ?? undefined });
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Validar límite de créditos de IA antes de gastar recursos en IA.
    const { data: creditProfile, error: creditError } = await supabase
      .from('profiles')
      .select('ai_credits_used, ai_credits_limit')
      .eq('id', user.id)
      .single();

    if (!creditError && creditProfile) {
      const used = creditProfile.ai_credits_used ?? 0;
      const limit = creditProfile.ai_credits_limit ?? 10;
      if (used >= limit) {
        auditLog({
          action: 'apply.blocked',
          userId: user.id,
          path: '/api/cv/improve',
          details: { reason: 'ai_credits_limit alcanzado', used, limit },
        });
        return NextResponse.json(
          { error: `Alcanzaste el límite de ${limit} créditos de IA de tu plan. Mejora tu plan en Configuración para seguir usando la IA.` },
          { status: 403 }
        );
      }
    }

    const { data: baseResume, error: resumeError } = await supabase
      .from('resumes')
      .select('cv_data')
      .eq('user_id', user.id)
      .is('target_company', null)
      .order('created_at', { ascending: false })
      .limit(1)
      .single();

    if (resumeError || !baseResume) {
      return NextResponse.json(
        { error: 'No tienes un CV base guardado todavía. Súbelo primero.' },
        { status: 400 }
      );
    }

    auditLog({ action: 'apply.request', userId: user.id, path: '/api/cv/improve' });

    const improvedCv = await improveCv(baseResume.cv_data as CVData);

    const { data: prof } = await supabase.from('profiles').select('ai_credits_used').eq('id', user.id).single();
    if (prof) {
      await supabase.from('profiles').update({ ai_credits_used: (prof.ai_credits_used || 0) + 1 }).eq('id', user.id);
    }

    return NextResponse.json({ success: true, cvData: improvedCv });
  } catch (error: unknown) {
    console.error('[CV Improve] Error:', error);
    return NextResponse.json(
      { error: 'No pudimos mejorar tu CV en este momento. Intenta de nuevo.' },
      { status: 500 }
    );
  }
}
