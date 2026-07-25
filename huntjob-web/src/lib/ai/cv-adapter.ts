import { generateObject } from 'ai';
import { executeWithFallback } from './provider';
import { z } from 'zod';
import { type JobOffer } from '../scraper/schema';
import { type CVData } from '../document/docx-generator';

const CVSchema = z.object({
  personalInfo: z.object({
    name: z.string(),
    email: z.string(),
    phone: z.string(),
    linkedin: z.string(),
    location: z.string(),
  }),
  summary: z.string(),
  experience: z.array(
    z.object({
      company: z.string(),
      position: z.string(),
      startDate: z.string(),
      endDate: z.string(),
      achievements: z.array(z.string()),
    })
  ),
  education: z.array(
    z.object({
      institution: z.string(),
      degree: z.string(),
      graduationDate: z.string(),
    })
  ),
  skills: z.array(z.string()),
});

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
2. DO rewrite the 'summary' to explicitly mention how their background fits the role.
3. DO reorder or emphasize 'skills' that match the job requirements.
4. DO rewrite the bullet points in 'achievements' to highlight metrics, impact, and keywords found in the job description (e.g. use the CAR framework: Context, Action, Result).
5. Maintain the same JSON structure as the original.

--- JOB OFFER ---
Title: ${jobOffer.title}
Company: ${jobOffer.company}
Description: ${jobOffer.rawDescription}
Requirements: ${jobOffer.requirements.join(', ')}
Keywords: ${jobOffer.keywords.join(', ')}

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
