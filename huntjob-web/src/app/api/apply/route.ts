import { NextResponse } from 'next/server';
import { scrapeJobOffer } from '@/lib/scraper/extractor';
import { adaptCvToJob } from '@/lib/ai/cv-adapter';
import { CVData } from '@/lib/document/docx-generator';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/ssr';
import { z } from 'zod';
import { validatePayloadSize } from '@/lib/security/sanitizer';
import { auditLog } from '@/lib/security/audit-log';

// Dominios permitidos para scraping de ofertas laborales
const ALLOWED_DOMAINS = [
  'getonbrd.com',
  'linkedin.com',
  'indeed.com',
  'computrabajo.com',
  'laborum.cl',
  'trabajando.cl',
  'bne.cl',
  'chiletrabajos.cl',
];

function isAllowedUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ALLOWED_DOMAINS.some(domain => parsed.hostname.endsWith(domain));
  } catch {
    return false;
  }
}

const applySchema = z.object({
  url: z.string().url("Debe ser una URL válida").max(500, "URL demasiado larga"),
  profile: z.record(z.string(), z.any()).refine(
    val => JSON.stringify(val).length < 50000, 
    "El perfil es demasiado extenso"
  )
});

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
      auditLog({ action: 'auth.unauthorized', path: '/api/apply', ip: req.headers.get('x-forwarded-for') ?? undefined });
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Validar límite de créditos de IA antes de gastar recursos en scraping/IA.
    // Si no se puede leer el perfil (fila ausente, error de red), no bloqueamos:
    // es una degradación de negocio, no un control de seguridad.
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
          path: '/api/apply',
          details: { reason: 'ai_credits_limit alcanzado', used, limit },
        });
        return NextResponse.json(
          { error: `Alcanzaste el límite de ${limit} créditos de IA de tu plan. Mejora tu plan en Configuración para seguir postulando.` },
          { status: 403 }
        );
      }
    }

    const json = await req.json();

    // Validar tamaño del payload
    const sizeCheck = validatePayloadSize(json, 100_000);
    if (!sizeCheck.safe) {
      auditLog({ action: 'apply.blocked', userId: user.id, path: '/api/apply', details: { reason: sizeCheck.reason } });
      return NextResponse.json({ error: sizeCheck.reason }, { status: 413 });
    }

    const parsedData = applySchema.safeParse(json);

    if (!parsedData.success) {
      return NextResponse.json({ error: 'Invalid input', details: parsedData.error.issues }, { status: 400 });
    }

    const { url, profile } = parsedData.data;

    // Validar dominio de la URL
    if (!isAllowedUrl(url)) {
      auditLog({
        action: 'apply.blocked',
        userId: user.id,
        path: '/api/apply',
        details: { reason: 'URL de dominio no permitido', url },
      });
      return NextResponse.json(
        { error: 'Solo se permiten URLs de portales de empleo conocidos (LinkedIn, GetOnBrd, Indeed, etc.).' },
        { status: 400 }
      );
    }

    auditLog({
      action: 'apply.request',
      userId: user.id,
      path: '/api/apply',
      details: { url },
    });

    // 1. Scrape Job Offer
    const source = url.includes('getonbrd.com') ? 'GetOnBoard' : url.includes('linkedin.com') ? 'LinkedIn' : 'Other';
    const jobOffer = await scrapeJobOffer(url, source);

    // 2. Adapt CV
    const adaptedCv = await adaptCvToJob(profile as CVData, jobOffer);

    // 3. Save to Supabase (applications & resumes tables)
    try {
      await supabase.from('applications').insert({
        user_id: user.id,
        company_name: jobOffer.company || 'Empresa',
        job_title: jobOffer.title || 'Cargo Oportunidad',
        job_url: url,
        status: 'pending',
        adapted_cv: adaptedCv,
      });

      await supabase.from('resumes').insert({
        user_id: user.id,
        name: `CV ${jobOffer.company} - ${jobOffer.title}`,
        cv_data: adaptedCv,
        target_company: jobOffer.company,
        target_role: jobOffer.title,
      });

      // Incrementar uso de créditos de IA en profile
      const { data: prof } = await supabase.from('profiles').select('ai_credits_used').eq('id', user.id).single();
      if (prof) {
        await supabase.from('profiles').update({ ai_credits_used: (prof.ai_credits_used || 0) + 1 }).eq('id', user.id);
      }
    } catch (dbErr) {
      console.warn('[Apply API] Warning: Failed to insert DB records:', dbErr);
    }

    // 4. Return results for the UI to consume
    return NextResponse.json({
      success: true,
      jobOffer: {
        title: jobOffer.title,
        company: jobOffer.company,
      },
      adaptedCv
    });

  } catch (error: unknown) {
    console.error('[Orchestrator] Error:', error);
    return NextResponse.json(
      { error: 'Failed to process application workflow', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
