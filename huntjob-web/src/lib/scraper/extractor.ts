import { generateObject } from 'ai';
import { executeWithFallback } from '../ai/provider';
import { JobOfferSchema, type JobOffer } from './schema';
import { PlaywrightScraper } from './playwright';

/**
 * Extracts structured job data from raw HTML using AI.
 */
export async function extractJobOfferFromHtml(rawHtml: string, source: string, url: string): Promise<JobOffer> {
  // We trim the HTML to avoid exceeding token limits (usually the main content is within the first chunk)
  // Or better, we can strip out script and style tags to reduce the size.
  const cleanHtml = rawHtml
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '')
    .replace(/<svg\b[^<]*(?:(?!<\/svg>)<[^<]*)*<\/svg>/gi, '')
    .substring(0, 20000); // 20k chars is well within context limits for standard models

  const prompt = `
You are an expert HR data extractor. I will provide you with the HTML content of a job posting.
Your task is to extract the details of the job offer and return them EXACTLY matching the provided schema.

Source of the job posting: ${source}
Original URL: ${url}

HTML Content:
---
${cleanHtml}
---

Extract the information carefully. For the "rawDescription", try to extract the main body of the job description as plain text (removing HTML tags, keeping the semantic structure like lists).
`;

  const result = await executeWithFallback(async (model) => {
    return generateObject({
      model,
      schema: JobOfferSchema,
      prompt: prompt,
    });
  });

  return result.object;
}

/**
 * High-level function to scrape a job offer given a URL.
 */
export async function scrapeJobOffer(url: string, source: string, waitForSelector?: string): Promise<JobOffer> {
  const scraper = new PlaywrightScraper();
  try {
    await scraper.init();
    const rawHtml = await scraper.getRawHtml(url, waitForSelector);
    const jobOffer = await extractJobOfferFromHtml(rawHtml, source, url);
    return jobOffer;
  } finally {
    await scraper.close();
  }
}
