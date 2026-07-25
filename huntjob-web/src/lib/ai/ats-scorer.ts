import { generateObject } from 'ai';
import { z } from 'zod';
import { executeWithFallback } from './provider';

// Schema for ATS Evaluation result
export const ATSEvaluationSchema = z.object({
  overallScore: z.number().min(0).max(100).describe("Puntuación general del 0 al 100"),
  dimensions: z.object({
    hardSkills: z.number().min(0).max(100).describe("Puntuación de Hard Skills & Stack (Peso 40%)"),
    seniority: z.number().min(0).max(100).describe("Puntuación de Seniority & Experiencia (Peso 30%)"),
    education: z.number().min(0).max(100).describe("Puntuación de Formación & Certificaciones (Peso 15%)"),
    softSkills: z.number().min(0).max(100).describe("Puntuación de Soft Skills & Fit Cultural (Peso 15%)"),
  }),
  missingKeywords: z.array(z.string()).describe("Lista de palabras clave que la oferta exige pero el CV no tiene"),
  criticalFeedback: z.string().describe("1 o 2 párrafos cortos y directos con la recomendación más crítica para pasar el filtro"),
});

export type ATSEvaluation = z.infer<typeof ATSEvaluationSchema>;

/**
 * Evaluates a Resume against a Job Description simulating an ATS algorithm.
 */
export async function evaluateATS(resumeContent: string, jobDescription: string): Promise<ATSEvaluation> {
  const systemPrompt = `
Eres un sistema ATS (Applicant Tracking System) implacable y avanzado usado por empresas Fortune 500.
Tu objetivo es analizar un currículum contra una oferta de trabajo y devolver una puntuación estrictamente objetiva.

REGLAS DE PUNTUACIÓN:
- Sé severo pero justo. Si no menciona una tecnología explícitamente, asume que NO la sabe.
- Hard Skills (40%): Evalúa la coincidencia exacta de lenguajes, frameworks, bases de datos y herramientas.
- Seniority (30%): Compara los años de experiencia requeridos contra los demostrados. Si piden 5 y tiene 2, el puntaje debe ser bajo.
- Formación (15%): Verifica si el candidato tiene la educación formal o certificaciones requeridas.
- Soft Skills (15%): Busca evidencia de liderazgo, comunicación, metodologías ágiles, etc.

Devuelve SIEMPRE la respuesta en el formato JSON requerido.
`;

  const userPrompt = `
OFERTA DE TRABAJO:
---
${jobDescription}
---

CURRÍCULUM DEL CANDIDATO:
---
${resumeContent}
---

Evalúa el currículum y entrega los resultados estructurados.
`;

  const result = await executeWithFallback(async (model) => {
    return generateObject({
      model,
      schema: ATSEvaluationSchema,
      system: systemPrompt,
      prompt: userPrompt,
    });
  });

  return result.object;
}
