import { NextResponse } from 'next/server';
import { PdfGenerator } from '@/lib/document/pdf-generator';
import { CVData } from '@/lib/document/docx-generator';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/ssr';
import { z } from 'zod';
import { validatePayloadSize } from '@/lib/security/sanitizer';
import { auditLog } from '@/lib/security/audit-log';

const exportSchema = z.object({
  personalInfo: z.record(z.string(), z.any()),
  experience: z.array(z.record(z.string(), z.any())),
}).passthrough();

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
      auditLog({ action: 'auth.unauthorized', path: '/api/export/pdf', ip: req.headers.get('x-forwarded-for') ?? undefined });
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const json = await req.json();

    // Validar tamaño del payload
    const sizeCheck = validatePayloadSize(json, 50_000);
    if (!sizeCheck.safe) {
      auditLog({ action: 'export.blocked', userId: user.id, path: '/api/export/pdf', details: { reason: sizeCheck.reason } });
      return NextResponse.json({ error: sizeCheck.reason }, { status: 413 });
    }

    const parsedData = exportSchema.safeParse(json);

    if (!parsedData.success || !parsedData.data.personalInfo || !parsedData.data.experience) {
      return NextResponse.json({ error: 'Formato de CV inválido' }, { status: 400 });
    }

    const data: CVData = parsedData.data as any;

    auditLog({
      action: 'export.request',
      userId: user.id,
      path: '/api/export/pdf',
    });

    const buffer = await PdfGenerator.generateCV(data);

    return new NextResponse(buffer as BlobPart, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${data.personalInfo.name.replace(/[^a-zA-Z0-9_\-\s]/g, '').replace(/\s+/g, '_')}_CV.pdf"`,
      },
    });

  } catch (error) {
    console.error('Error generando PDF:', error);
    return NextResponse.json({ error: 'Error al generar el documento PDF' }, { status: 500 });
  }
}
