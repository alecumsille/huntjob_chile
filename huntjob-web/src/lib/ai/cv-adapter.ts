import { generateObject } from 'ai';
import { executeWithFallback } from './provider';
import { type JobOffer } from '../scraper/schema';
import { type CVData } from '../document/docx-generator';
import { CVSchema } from './cv-schema';

/**
 * Adapts an existing CV to better match a specific Job Offer.
 */
export async function adaptCvToJob(originalCv: CVData, jobOffer: JobOffer): Promise<CVData> {
  const prompt = `
You are an elite Tech Recruiter and Resume Writer. 
I will provide you with a candidate's original CV and a Job Offer they are applying to.
Your task is to REWRITE and ADAPT the candidate's CV so that it perfectly aligns with the Job Offer, increasing their ATS match score and highlighting the most relevant experience and skills.

RULES:
1. Do NOT lie or invent experience that the candidate does not have.
2. DO rewrite the 'summary' to explicitly mention how their background fits the role, using an authentic, professional human tone.
3. DO reorder or emphasize 'skills' that match the job requirements.
4. DO rewrite the bullet points in 'achievements' using the CAR framework (Context, Action, Result) with concrete metrics and impact.
5. Maintain the exact JSON structure as the original.

NO AI SLOP & ANTI-BOT WRITING STYLE:
- Absolutely FORBIDDEN cliché AI buzzwords: "delve", "testament", "tapestry", "game-changer", "pivotal", "spearheaded", "seamlessly", "elevate", "synergy", "fostered", "realm", "ever-evolving", "landscape", "beacon", "meticulously", "holistic".
- Write like a real, top 1% human senior engineer: concise, direct, active action verbs (e.g. "Lideré", "Implementé", "Optimicé", "Reduje", "Aumenté").
- Avoid generic corporate fluff; every sentence must convey concrete value or technical specifics.

--- JOB OFFER ---
Title: ${jobOffer.title}
Company: ${jobOffer.company}
Description: ${jobOffer.rawDescription}
Requirements: ${jobOffer.mandatoryRequirements.join(', ')}

--- ORIGINAL CV ---
${JSON.stringify(originalCv, null, 2)}

Return the newly adapted CV matching the exact Zod schema.
`;

  const result = await executeWithFallback(async (model) => {
    return generateObject({
      model,
      schema: CVSchema,
      prompt: prompt,
    });
  });

  return result.object as CVData;
}
