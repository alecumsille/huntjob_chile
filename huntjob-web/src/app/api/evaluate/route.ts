import { NextResponse } from 'next/server';
import { scrapeJobOffer } from '@/lib/scraper/extractor';
import { evaluateATS } from '@/lib/ai/ats-scorer';
import { evaluateJobBlocks } from '@/lib/ai/job-evaluator';
import { CVData } from '@/lib/document/docx-generator';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/ssr';
import { z } from 'zod';
import { validatePayloadSize, sanitizeText } from '@/lib/security/sanitizer';
import { auditLog } from '@/lib/security/audit-log';

// Misma lista que /api/apply -- mantener sincronizadas si cambia una.
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

const evaluateSchema = z.object({
  url: z.string().url("Debe ser una URL válida").max(500, "URL demasiado larga"),
  profile: z.record(z.string(), z.any()).refine(
    val => JSON.stringify(val).length < 50000,
    "El perfil es demasiado extenso"
  ),
});

function summarizeCv(profile: CVData): string {
  const parts: string[] = [];
  if (profile.summary) parts.push(profile.summary);
  if (profile.experience?.length) {
    parts.push('Experiencia: ' + profile.experience.map(e => `${e.position} en ${e.company}`).join('; '));
  }
  if (profile.skills?.length) parts.push('Skills: ' + profile.skills.join(', '));
  return parts.join('\n') || JSON.stringify(profile).slice(0, 2000);
}

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
      auditLog({ action: 'auth.unauthorized', path: '/api/evaluate', ip: req.headers.get('x-forwarded-for') ?? undefined });
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

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
          action: 'evaluate.blocked',
          userId: user.id,
          path: '/api/evaluate',
          details: { reason: 'ai_credits_limit alcanzado', used, limit },
        });
        return NextResponse.json(
          { error: `Alcanzaste el límite de ${limit} créditos de IA de tu plan. Mejora tu plan en Configuración para seguir evaluando ofertas.` },
          { status: 403 }
        );
      }
    }

    const json = await req.json();

    const sizeCheck = validatePayloadSize(json, 100_000);
    if (!sizeCheck.safe) {
      auditLog({ action: 'evaluate.blocked', userId: user.id, path: '/api/evaluate', details: { reason: sizeCheck.reason } });
      return NextResponse.json({ error: sizeCheck.reason }, { status: 413 });
    }

    const parsedData = evaluateSchema.safeParse(json);
    if (!parsedData.success) {
      return NextResponse.json({ error: 'Invalid input', details: parsedData.error.issues }, { status: 400 });
    }

    const { url, profile } = parsedData.data;

    if (!isAllowedUrl(url)) {
      auditLog({
        action: 'evaluate.blocked',
        userId: user.id,
        path: '/api/evaluate',
        details: { reason: 'URL de dominio no permitido', url },
      });
      return NextResponse.json(
        { error: 'Solo se permiten URLs de portales de empleo conocidos (LinkedIn, GetOnBrd, Indeed, etc.).' },
        { status: 400 }
      );
    }

    auditLog({ action: 'evaluate.request', userId: user.id, path: '/api/evaluate', details: { url } });

    // 1. Scrape
    const source = url.includes('getonbrd.com') ? 'GetOnBoard' : url.includes('linkedin.com') ? 'LinkedIn' : 'Other';
    const jobOffer = await scrapeJobOffer(url, source);

    // 2. Sanitizar la descripcion scrapeada antes de mandarla a la IA
    // (limpieza de caracteres invisibles/control -- sin el chequeo de
    // patrones de injection de sanitizeChatMessage, que da falsos positivos
    // con frases normales de una oferta como "actuar como punto de contacto").
    const cleanDescription = sanitizeText(jobOffer.rawDescription);
    if (cleanDescription.length < 100) {
      return NextResponse.json(
        { error: 'No se pudo extraer suficiente contenido de la oferta para evaluarla.' },
        { status: 422 }
      );
    }
    const sanitizedJobOffer = { ...jobOffer, rawDescription: cleanDescription };

    // 3. Las 2 llamadas de IA
    const cvSummary = summarizeCv(profile as CVData);
    const [cvMatch, blocks] = await Promise.all([
      evaluateATS(cvSummary, cleanDescription),
      evaluateJobBlocks(sanitizedJobOffer, cvSummary),
    ]);

    // 4. Score final ponderado (calculado en codigo, no por la IA)
    const cvMatchScore5 = 1.0 + (cvMatch.overallScore / 100) * 4.0;
    const rawScore =
      cvMatchScore5 * 0.30 +
      blocks.levelStrategy.score * 0.15 +
      blocks.salaryResearch.score * 0.15 +
      blocks.personalization.score * 0.15 +
      blocks.roleSummary.score * 0.15 +
      blocks.interviewPrep.score * 0.10;
    const overallScore = Math.round(rawScore * 10) / 10;

    // 5. Guardar + gastar 1 credito (una sola vez, aunque fueron 2 llamadas de IA)
    let evaluationId: string | null = null;
    try {
      const { data: inserted } = await supabase.from('job_evaluations').insert({
        user_id: user.id,
        job_url: url,
        company_name: jobOffer.company || 'Empresa',
        job_title: jobOffer.title || 'Cargo',
        jd_raw: cleanDescription,
        overall_score: overallScore,
        blocks: { ...blocks, cvMatch },
        is_suspicious: blocks.blockG.isSuspicious,
        suspicious_reason: blocks.blockG.reason,
      }).select('id').single();
      evaluationId = inserted?.id ?? null;

      const { data: prof } = await supabase.from('profiles').select('ai_credits_used').eq('id', user.id).single();
      if (prof) {
        await supabase.from('profiles').update({ ai_credits_used: (prof.ai_credits_used || 0) + 1 }).eq('id', user.id);
      }
    } catch (dbErr) {
      console.warn('[Evaluate API] Warning: Failed to insert DB records:', dbErr);
    }

    return NextResponse.json({
      success: true,
      evaluationId,
      overallScore,
      isSuspicious: blocks.blockG.isSuspicious,
      suspiciousReason: blocks.blockG.reason,
      blocks,
      cvMatch,
      jobOffer: { title: jobOffer.title, company: jobOffer.company },
    });

  } catch (error: unknown) {
    console.error('[Evaluate API] Error:', error);
    return NextResponse.json(
      { error: 'Failed to evaluate job offer', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
