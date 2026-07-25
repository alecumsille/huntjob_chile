import { streamText } from 'ai';
import { google } from '@ai-sdk/google';
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/ssr';
import { z } from 'zod';

// Define the validation schema
const chatSchema = z.object({
  messages: z.array(
    z.object({
      role: z.enum(['user', 'assistant', 'system', 'data']),
      content: z.string().max(4000, "El mensaje es demasiado largo"),
    })
  ).max(50, "Demasiados mensajes en la conversación"),
  context: z.object({
    company: z.string().max(100).optional(),
    role: z.string().max(100).optional(),
    type: z.enum(['technical', 'hr', 'general']).optional(),
  }).optional(),
});

// Opt out of caching; we always want dynamic responses
export const dynamic = 'force-dynamic';

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
    const parsedData = chatSchema.safeParse(json);
    
    if (!parsedData.success) {
      return NextResponse.json({ error: 'Invalid input', details: parsedData.error.issues }, { status: 400 });
    }

    const { messages, context } = parsedData.data;

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
      messages: messages as { role: 'user' | 'assistant' | 'system', content: string }[],
      temperature: 0.7,
    });

    return result.toTextStreamResponse();
  } catch (error) {
    console.error('Error in chat route:', error);
    return NextResponse.json({ error: 'Failed to generate response' }, { status: 500 });
  }
}
