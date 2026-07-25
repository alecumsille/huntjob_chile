import { z } from 'zod';

export const JobOfferSchema = z.object({
  id: z.string().describe("Identificador único de la oferta o hash del enlace"),
  title: z.string().describe("Título oficial del cargo"),
  company: z.string().describe("Nombre de la empresa que contrata"),
  location: z.string().describe("Ubicación del puesto (Ciudad, País)"),
  modality: z.enum(['Remoto', 'Híbrido', 'Presencial', 'No especificado']).describe("Modalidad de trabajo"),
  salaryRange: z.string().nullable().describe("Rango salarial si está explícito, sino null"),
  mandatoryRequirements: z.array(z.string()).describe("Lista de requisitos técnicos/blandos excluyentes (ej. 'React', 'Inglés avanzado')"),
  niceToHaveRequirements: z.array(z.string()).describe("Lista de requisitos deseables o 'plus'"),
  postedAt: z.string().nullable().describe("Fecha de publicación original de la oferta (ISO 8601 o YYYY-MM-DD)"),
  originalUrl: z.string().url().describe("Enlace canónico a la postulación original"),
  source: z.string().describe("Portal desde donde se extrajo (ej. 'LinkedIn', 'GetOnBoard')"),
  rawDescription: z.string().describe("Texto completo y sin procesar de la descripción del trabajo"),
});

export type JobOffer = z.infer<typeof JobOfferSchema>;
