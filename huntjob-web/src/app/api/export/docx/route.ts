import { NextResponse } from 'next/server';
import { DocxGenerator, CVData } from '@/lib/document/docx-generator';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/ssr';
import { z } from 'zod';

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
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const json = await req.json();
    
    // Quick length check to prevent huge payloads
    if (JSON.stringify(json).length > 50000) {
       return NextResponse.json({ error: 'Payload too large' }, { status: 413 });
    }

    const parsedData = exportSchema.safeParse(json);

    if (!parsedData.success || !parsedData.data.personalInfo || !parsedData.data.experience) {
      return NextResponse.json({ error: 'Formato de CV inválido' }, { status: 400 });
    }
    
    const data: CVData = parsedData.data as any;

    // Generar el Buffer del DOCX
    const buffer = await DocxGenerator.generateCV(data);

    // Crear la respuesta con el archivo adjunto
    const response = new NextResponse(buffer as BlobPart, {
      status: 200,
      headers: {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'Content-Disposition': `attachment; filename="${data.personalInfo.name.replace(/\s+/g, '_')}_CV.docx"`,
      },
    });

    return response;

  } catch (error) {
    console.error('Error generando DOCX:', error);
    return NextResponse.json({ error: 'Error al generar el documento Word' }, { status: 500 });
  }
}
