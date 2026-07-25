import { NextResponse } from 'next/server';
import { scrapeJobOffer } from '@/lib/scraper/extractor';
import { adaptCvToJob } from '@/lib/ai/cv-adapter';
import { CVData } from '@/lib/document/docx-generator';

export async function POST(req: Request) {
  try {
    const { url, profile } = await req.json();

    if (!url || !profile) {
      return NextResponse.json({ error: 'Missing url or profile data' }, { status: 400 });
    }

    console.log(`[Orchestrator] Starting workflow for URL: ${url}`);

    // 1. Scrape Job Offer
    console.log(`[Orchestrator] Scraping job offer...`);
    // Determine source
    const source = url.includes('getonbrd.com') ? 'GetOnBoard' : url.includes('linkedin.com') ? 'LinkedIn' : 'Other';
    const jobOffer = await scrapeJobOffer(url, source);
    console.log(`[Orchestrator] Job scraped: ${jobOffer.title} at ${jobOffer.company}`);

    // 2. Adapt CV
    console.log(`[Orchestrator] Adapting CV via AI...`);
    const adaptedCv = await adaptCvToJob(profile as CVData, jobOffer);
    console.log(`[Orchestrator] CV Adapted successfully.`);

    // 3. Return results for the UI to consume
    return NextResponse.json({
      success: true,
      jobOffer: {
        title: jobOffer.title,
        company: jobOffer.company,
      },
      adaptedCv
    });

  } catch (error: any) {
    console.error('[Orchestrator] Error:', error);
    return NextResponse.json(
      { error: 'Failed to process application workflow', details: error.message },
      { status: 500 }
    );
  }
}
