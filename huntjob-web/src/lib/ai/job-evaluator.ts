import { generateObject } from 'ai';
import { z } from 'zod';
import { executeWithFallback } from './provider';
import { type JobOffer } from '../scraper/schema';

export const JobEvaluationBlocksSchema = z.object({
  roleSummary: z.object({
    score: z.number().min(1).max(5).describe("Qué tan interesante es el rol en sí, 1.0-5.0"),
    summary: z.string().describe("2-3 frases explicando qué hace el puesto, en lenguaje simple"),
  }),
  levelStrategy: z.object({
    score: z.number().min(1).max(5).describe("Qué tan bien calza el nivel pedido con el perfil, 1.0-5.0"),
    fit: z.enum(['por_debajo', 'calza', 'por_encima']).describe("Si el nivel pedido es inferior, igual o superior al perfil del candidato"),
    advice: z.string().describe("Consejo concreto: negociar hacia arriba, aplicar tal cual, o replantear expectativas"),
  }),
  salaryResearch: z.object({
    score: z.number().min(1).max(5).describe("Qué tan atractivo es el rango salarial estimado vs. mercado, 1.0-5.0"),
    estimatedRange: z.string().describe("Rango salarial estimado de mercado para este rol/ubicación/seniority"),
    confidence: z.enum(['alta', 'media', 'baja']).describe("Confianza de la estimación -- baja si la oferta no da pistas de ubicación/seniority claras"),
  }),
  personalization: z.object({
    score: z.number().min(1).max(5).describe("Qué tan fácil es personalizar la postulación para esta oferta específica, 1.0-5.0"),
    angle: z.string().describe("Qué ángulo específico del perfil del candidato destacar para esta oferta en particular"),
  }),
  interviewPrep: z.object({
    score: z.number().min(1).max(5).describe("Qué tan preparable es la entrevista con la info disponible, 1.0-5.0"),
    questions: z.array(z.object({
      question: z.string().describe("Pregunta de entrevista probable para este rol"),
      starHint: z.string().describe("Qué tipo de historia STAR+R conviene traer para responderla"),
    })).min(2).max(3),
  }),
  blockG: z.object({
    isSuspicious: z.boolean().describe("true si la oferta muestra señales de ser falsa, scam o ghost job"),
    reason: z.string().nullable().describe("Motivo concreto si isSuspicious es true (ej. 'lleva 6+ meses publicada sin rango salarial'), null si no aplica"),
  }),
});

export type JobEvaluationBlocks = z.infer<typeof JobEvaluationBlocksSchema>;

/**
 * Genera los 6 bloques de evaluación de una oferta (todo menos CV Match,
 * que ya cubre ats-scorer.ts por separado).
 */
export async function evaluateJobBlocks(jobOffer: JobOffer, cvSummary: string): Promise<JobEvaluationBlocks> {
  const systemPrompt = `
Eres un coach de carrera senior evaluando una oferta de trabajo para un candidato específico.
Sé concreto y honesto, no genérico. Si la oferta tiene señales de ser falsa o de baja calidad, dilo sin miedo en el Bloque G.
Todos los "score" van de 1.0 a 5.0, con 5.0 siendo excelente y 1.0 siendo muy malo -- usa decimales, no solo enteros.
Devuelve SIEMPRE la respuesta en el formato JSON requerido.
`;

  const userPrompt = `
PERFIL DEL CANDIDATO (resumen):
---
${cvSummary}
---

OFERTA DE TRABAJO:
Cargo: ${jobOffer.title}
Empresa: ${jobOffer.company}
Rango salarial publicado: ${jobOffer.salaryRange ?? 'No especificado'}
Fecha de publicación: ${jobOffer.postedAt ?? 'No disponible'}
Requisitos excluyentes: ${jobOffer.mandatoryRequirements.join(', ') || 'No especificados'}

DESCRIPCIÓN COMPLETA:
---
${jobOffer.rawDescription}
---

Evalúa esta oferta para este candidato y entrega los 6 bloques estructurados.
`;

  const result = await executeWithFallback(async (model) => {
    return generateObject({
      model,
      schema: JobEvaluationBlocksSchema,
      system: systemPrompt,
      prompt: userPrompt,
    });
  });

  return result.object;
}
