import { NextResponse } from 'next/server';
import { generateObject } from 'ai';
import { executeWithFallback } from '@/lib/ai/provider';
import { CVSchema } from '@/lib/ai/cv-schema';
import { createClient } from '@/utils/supabase/server';
import { auditLog } from '@/lib/security/audit-log';
import { detectPromptInjection } from '@/lib/security/sanitizer';

const MAX_PDF_BYTES = 4 * 1024 * 1024; // 4MB — Vercel functions cap request bodies around 4.5MB total

const EXTRACTION_PROMPT = `
Eres un extractor de datos de CVs. Analiza el PDF adjunto y devuelve la información
estructurada exactamente en el esquema JSON indicado.

REGLAS:
1. Si un campo no aparece en el PDF, usa un string vacío ("") o un array vacío ([]), nunca inventes datos.
2. Fechas en el formato que aparezcan en el original (ej. "Ene 2021", "2021", "Presente").
3. "achievements" son las viñetas/logros bajo cada experiencia laboral, tal como aparecen (no las reescribas).
4. No agregues comentarios ni texto fuera del JSON del esquema.
`;

export async function POST(req: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    auditLog({ action: 'auth.unauthorized', path: '/api/cv/parse', ip: req.headers.get('x-forwarded-for') ?? undefined });
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const formData = await req.formData();
    const file = formData.get('file');

    if (!(file instanceof File)) {
      return NextResponse.json({ error: 'Falta el archivo PDF.' }, { status: 400 });
    }

    if (file.type !== 'application/pdf') {
      return NextResponse.json({ error: 'Solo se aceptan archivos PDF.' }, { status: 400 });
    }

    if (file.size > MAX_PDF_BYTES) {
      return NextResponse.json({ error: 'El PDF supera el límite de 4MB.' }, { status: 413 });
    }

    auditLog({ action: 'apply.request', userId: user.id, path: '/api/cv/parse', details: { filename: file.name } });

    const pdfBuffer = Buffer.from(await file.arrayBuffer());

    const result = await executeWithFallback((model) =>
      generateObject({
        model,
        schema: CVSchema,
        messages: [
          {
            role: 'user',
            content: [
              { type: 'text', text: EXTRACTION_PROMPT },
              { type: 'file', data: pdfBuffer, mediaType: 'application/pdf' },
            ],
          },
        ],
      })
    );

    const cvData = result.object;

    const freeTextFields = [cvData.summary, ...cvData.experience.flatMap((e) => e.achievements)];
    for (const text of freeTextFields) {
      if (!text) continue;
      const check = detectPromptInjection(text);
      if (!check.safe) {
        auditLog({ action: 'injection.detected', userId: user.id, path: '/api/cv/parse' });
        return NextResponse.json(
          { error: 'El PDF contiene texto que no pudimos procesar de forma segura. Completa el formulario manualmente.' },
          { status: 422 }
        );
      }
    }

    return NextResponse.json({ success: true, cvData });
  } catch (error: unknown) {
    console.error('[CV Parse] Error:', error);
    return NextResponse.json(
      { error: 'No pudimos leer tu PDF. Completa el formulario manualmente.' },
      { status: 422 }
    );
  }
}
