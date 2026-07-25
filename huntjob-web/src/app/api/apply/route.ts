import { NextResponse } from 'next/server';
import { scrapeJobOffer } from '@/lib/scraper/extractor';
import { adaptCvToJob } from '@/lib/ai/cv-adapter';
import { CVData } from '@/lib/document/docx-generator';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/ssr';
import { z } from 'zod';

const applySchema = z.object({
  url: z.string().url("Debe ser una URL válida").max(500, "URL demasiado larga"),
  profile: z.record(z.string(), z.any()).refine(
    val => JSON.stringify(val).length < 50000, 
    "El perfil es demasiado extenso"
  )
});

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
    const parsedData = applySchema.safeParse(json);

    if (!parsedData.success) {
      return NextResponse.json({ error: 'Invalid input', details: parsedData.error.issues }, { status: 400 });
    }

    const { url, profile } = parsedData.data;

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

  } catch (error: unknown) {
    console.error('[Orchestrator] Error:', error);
    return NextResponse.json(
      { error: 'Failed to process application workflow', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
