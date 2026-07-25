import { streamText } from 'ai';
import { google } from '@ai-sdk/google';
import { NextResponse } from 'next/server';

// Opt out of caching; we always want dynamic responses
export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  try {
    const { messages, context } = await req.json();

    // System prompt para contextualizar al agente
    const systemPrompt = `Eres un reclutador experto y entrevistador técnico simulando una entrevista para la empresa ${context?.company || 'una empresa tecnológica'} para el puesto de ${context?.role || 'Ingeniero'}.
    Tipo de entrevista: ${context?.type === 'technical' ? 'Técnica (preguntas de código, arquitectura, casos de uso)' : context?.type === 'hr' ? 'Recursos Humanos (preguntas conductuales, cultura, fit)' : 'General'}.
    
    Instrucciones:
    1. Actúa 100% como el entrevistador.
    2. Haz una pregunta a la vez y espera la respuesta.
    3. Evalúa sutilmente las respuestas del candidato (puedes pedir que profundice si la respuesta es corta).
    4. Sé profesional, realista y mantén el personaje.
    5. Nunca te salgas del rol.
    6. Tus respuestas deben ser breves y conversacionales (máximo 2-3 párrafos cortos).`;

    // Iniciamos el stream de texto con Gemini (Google) usando ai-sdk
    const result = streamText({
      model: google('gemini-1.5-flash-latest'),
      system: systemPrompt,
      messages: messages as any[],
      temperature: 0.7,
    });

    return result.toTextStreamResponse();
  } catch (error) {
    console.error('Error in chat route:', error);
    return NextResponse.json({ error: 'Failed to generate response' }, { status: 500 });
  }
}
