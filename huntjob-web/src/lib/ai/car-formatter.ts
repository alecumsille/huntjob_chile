import { generateObject } from 'ai';
import { z } from 'zod';
import { executeWithFallback } from './provider';

// Schema for CAR Formatting result
export const CARFormatterSchema = z.object({
  original: z.string().describe("El texto original enviado por el usuario"),
  carFormat: z.array(z.string()).describe("Lista de viñetas (bullet points) optimizadas usando Contexto, Acción y Resultado"),
  impactMetricsAdded: z.boolean().describe("Indica si la IA logró deducir o añadir métricas de impacto realistas al texto"),
  atsKeywordsInjected: z.array(z.string()).describe("Palabras clave de alto impacto que se inyectaron orgánicamente en la redacción"),
});

export type CARFormattedResult = z.infer<typeof CARFormatterSchema>;

/**
 * Transforms plain resume bullet points into Google CAR format.
 */
export async function formatToCAR(rawExperience: string, jobKeywordsContext?: string[]): Promise<CARFormattedResult> {
  const systemPrompt = `
Eres un Experto Redactor de Currículums de Nivel Ejecutivo. Tu especialidad es transformar descripciones de trabajo planas y aburridas en viñetas de alto impacto utilizando la metodología Google CAR (Contexto, Acción, Resultado).

REGLAS DE TRANSFORMACIÓN:
1. Contexto: ¿Cuál era la situación o el problema?
2. Acción: ¿Qué hizo exactamente la persona? (Usa verbos de acción fuertes como 'Lideró', 'Orquestó', 'Arquitectó').
3. Resultado: ¿Cuál fue el impacto MEDIBLE? (Si el texto original no tiene métricas, estima una mejora razonable conservadora, ej. "aumentando la eficiencia en un 20%").

Tu salida debe ser un conjunto de viñetas de 1 o 2 líneas máximo, listas para copiar y pegar en un currículum moderno.
  `;

  const keywordsContext = jobKeywordsContext?.length 
    ? `\nINTENTA INYECTAR ESTAS PALABRAS CLAVE SI ES NATURAL HACERLO:\n${jobKeywordsContext.join(", ")}` 
    : "";

  const userPrompt = `
EXPERIENCIA ORIGINAL:
---
${rawExperience}
---
${keywordsContext}

Transforma esta experiencia a formato CAR.
`;

  const result = await executeWithFallback(async (model) => {
    return generateObject({
      model,
      schema: CARFormatterSchema,
      system: systemPrompt,
      prompt: userPrompt,
    });
  });

  return result.object;
}
