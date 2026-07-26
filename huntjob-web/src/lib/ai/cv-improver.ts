import { generateObject } from 'ai';
import { executeWithFallback } from './provider';
import { type CVData } from '../document/docx-generator';
import { CVSchema } from './cv-schema';

/**
 * Rewrites a CV to be stronger in general, without tailoring it to any
 * specific job offer (that's adaptCvToJob's job).
 */
export async function improveCv(originalCv: CVData): Promise<CVData> {
  const prompt = `
You are an elite Tech Recruiter and Resume Writer.
I will give you a candidate's CV, extracted as-is from their PDF. Your task is to
REWRITE it to be significantly stronger as a general-purpose base resume — not for
any specific job offer, just objectively better.

RULES:
1. Do NOT lie or invent experience, companies, dates, or metrics that aren't implied by the original.
2. DO rewrite the 'summary' into a strong, concise, professional pitch.
3. DO rewrite the bullet points in 'achievements' using the CAR framework (Context, Action, Result) with concrete metrics and impact whenever the original supports it.
4. DO keep all companies, positions, dates, and education exactly as given.
5. Maintain the exact JSON structure as the original.

NO AI SLOP & ANTI-BOT WRITING STYLE:
- Absolutely FORBIDDEN cliché AI buzzwords: "delve", "testament", "tapestry", "game-changer", "pivotal", "spearheaded", "seamlessly", "elevate", "synergy", "fostered", "realm", "ever-evolving", "landscape", "beacon", "meticulously", "holistic".
- Write like a real, top 1% human senior professional: concise, direct, active action verbs (e.g. "Lideré", "Implementé", "Optimicé", "Reduje", "Aumenté").
- Avoid generic corporate fluff; every sentence must convey concrete value or technical specifics.

--- ORIGINAL CV ---
${JSON.stringify(originalCv, null, 2)}

Return the newly improved CV matching the exact Zod schema.
`;

  const result = await executeWithFallback(async (model) => {
    return generateObject({
      model,
      schema: CVSchema,
      prompt,
    });
  });

  return result.object as CVData;
}
