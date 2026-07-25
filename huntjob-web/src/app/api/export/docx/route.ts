import { NextResponse } from 'next/server';
import { DocxGenerator, CVData } from '@/lib/document/docx-generator';

export async function POST(req: Request) {
  try {
    const data: CVData = await req.json();

    if (!data || !data.personalInfo || !data.experience) {
      return NextResponse.json({ error: 'Formato de CV inválido' }, { status: 400 });
    }

    // Generar el Buffer del DOCX
    const buffer = await DocxGenerator.generateCV(data);

    // Crear la respuesta con el archivo adjunto
    const response = new NextResponse(buffer as any, {
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
