# Evaluación A-F de Ofertas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a HuntJob user paste a job posting URL and get a structured 7-block evaluation (score 1.0-5.0 + a scam/ghost-job flag) before deciding whether to spend a real "apply" credit on it.

**Architecture:** A new Supabase table (`job_evaluations`) decoupled from `applications`. A new AI module (`job-evaluator.ts`) generates 6 of the 7 blocks in one `generateObject` call; the 7th block (CV Match) reuses the existing, currently-unused `ats-scorer.ts` unmodified. A new route (`POST /api/evaluate`) orchestrates both calls behind the exact same auth/credit-gate/rate-limit/domain-allowlist pattern already proven in `/api/apply`. A new page (`/dashboard/evaluate`) is the UI, and `/api/apply` gets one small addition to accept and store the originating `evaluation_id`.

**Tech Stack:** Next.js 15 App Router, Supabase (`@supabase/ssr`), Vercel AI SDK (`generateObject` + Zod), `executeWithFallback` (OpenAI→Gemini), Upstash `@upstash/ratelimit`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-26-job-evaluation-design.md` (commit `c122cb1`).
- The whole evaluation (both AI calls) costs **exactly 1** `ai_credits_used`, never 2.
- Only URLs from the existing `ALLOWED_DOMAINS` allowlist (getonbrd.com, linkedin.com, indeed.com, computrabajo.com, laborum.cl, trabajando.cl, bne.cl, chiletrabajos.cl) may be scraped — copy the exact same list, don't invent a new one.
- `ats-scorer.ts` (`evaluateATS`) must not be modified — reused as-is for the CV Match block.
- Block G (`isSuspicious`/`reason`) never hides or changes the numeric score — it's a separate banner.
- No automated test framework exists for AI routes in this app — every task's verification step is a real manual call (`curl` or browser), not a test file.
- This app has no Python; do not write Python testing steps — everything here is TypeScript/Next.js.

---

### Task 1: Database migration — `job_evaluations` table + `applications.evaluation_id`

**Files:**
- Create: `supabase/migrations/2026-07-26-job-evaluations.sql`

**Interfaces:**
- Produces: table `job_evaluations` with columns `id, user_id, job_url, company_name, job_title, jd_raw, overall_score, blocks, is_suspicious, suspicious_reason, created_at`; column `applications.evaluation_id` (nullable UUID FK to `job_evaluations.id`). Later tasks insert into and read from this table by these exact column names.

- [ ] **Step 1: Write the migration file**

```sql
-- supabase/migrations/2026-07-26-job-evaluations.sql
CREATE TABLE IF NOT EXISTS job_evaluations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  job_url TEXT NOT NULL,
  company_name TEXT NOT NULL,
  job_title TEXT NOT NULL,
  jd_raw TEXT NOT NULL,
  overall_score NUMERIC(2,1) NOT NULL CHECK (overall_score >= 1.0 AND overall_score <= 5.0),
  blocks JSONB NOT NULL,
  is_suspicious BOOLEAN NOT NULL DEFAULT false,
  suspicious_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE applications ADD COLUMN IF NOT EXISTS evaluation_id UUID REFERENCES job_evaluations(id);

ALTER TABLE job_evaluations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own evaluations" ON job_evaluations;
CREATE POLICY "Users can view their own evaluations" ON job_evaluations
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own evaluations" ON job_evaluations;
CREATE POLICY "Users can insert their own evaluations" ON job_evaluations
  FOR INSERT WITH CHECK (auth.uid() = user_id);
```

- [ ] **Step 2: Run it against the real Supabase project**

Run via the Supabase SQL editor (same manual process used for `schema_prod_migration.sql` earlier this project), or:
```bash
cd /home/ale/Antigravity/huntjob-web/huntjob-web
cat supabase/migrations/2026-07-26-job-evaluations.sql
```
then paste into Supabase Dashboard → SQL Editor → Run.

Expected: no errors. Verify with:
```sql
SELECT column_name FROM information_schema.columns WHERE table_name = 'job_evaluations';
SELECT column_name FROM information_schema.columns WHERE table_name = 'applications' AND column_name = 'evaluation_id';
```
Expected: `job_evaluations` lists all 10 columns; the second query returns one row (`evaluation_id`).

- [ ] **Step 3: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web/huntjob-web
git add supabase/migrations/2026-07-26-job-evaluations.sql
git commit -m "feat(db): agrega tabla job_evaluations y applications.evaluation_id"
```

---

### Task 2: `job-evaluator.ts` — the 6-block AI module

**Files:**
- Create: `src/lib/ai/job-evaluator.ts`

**Interfaces:**
- Consumes: `executeWithFallback` from `./provider` (signature: `executeWithFallback<T>(action: (model: LanguageModel) => Promise<T>): Promise<T>`), `JobOffer` type from `../scraper/schema` (fields used: `title`, `company`, `rawDescription`, `salaryRange`, `postedAt`, `mandatoryRequirements`).
- Produces: `JobEvaluationBlocksSchema` (Zod schema), `JobEvaluationBlocks` (inferred type), `evaluateJobBlocks(jobOffer: JobOffer, cvSummary: string): Promise<JobEvaluationBlocks>` — Task 3 calls this exact function with these exact two arguments.

- [ ] **Step 1: Write the module**

```typescript
// src/lib/ai/job-evaluator.ts
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
```

- [ ] **Step 2: Verify it compiles**

Run: `cd /home/ale/Antigravity/huntjob-web/huntjob-web && npx tsc --noEmit`
Expected: no new type errors referencing `job-evaluator.ts`.

- [ ] **Step 3: Manual smoke test with a real job offer**

Create a throwaway script `scratch/test-job-evaluator.mjs` (do not commit it) that imports the compiled module via `tsx`, or simpler — verify manually once Task 3's route exists (this task's own isolated test is the compile check; end-to-end AI output is verified in Task 3's manual test since it needs a real scraped `JobOffer`).

- [ ] **Step 4: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web/huntjob-web
git add src/lib/ai/job-evaluator.ts
git commit -m "feat(ai): agrega job-evaluator.ts con los 6 bloques de evaluacion"
```

---

### Task 3: `POST /api/evaluate` — orchestration route + rate limit

**Files:**
- Create: `src/app/api/evaluate/route.ts`
- Modify: `src/middleware.ts:31`

**Interfaces:**
- Consumes: `evaluateJobBlocks(jobOffer, cvSummary)` from Task 2, `evaluateATS(resumeContent, jobDescription): Promise<ATSEvaluation>` from `@/lib/ai/ats-scorer` (`ATSEvaluation.overallScore` is 0-100), `scrapeJobOffer(url, source)` from `@/lib/scraper/extractor`, `sanitizeText` from `@/lib/security/sanitizer`, `validatePayloadSize` from `@/lib/security/sanitizer`, `auditLog` from `@/lib/security/audit-log`.
- Produces: JSON response shape `{ success: true, evaluationId: string, overallScore: number, isSuspicious: boolean, suspiciousReason: string | null, blocks: JobEvaluationBlocks, cvMatch: ATSEvaluation, jobOffer: { title: string, company: string } }` — Task 5's UI page consumes exactly this shape.

- [ ] **Step 1: Write the route**

```typescript
// src/app/api/evaluate/route.ts
import { NextResponse } from 'next/server';
import { scrapeJobOffer } from '@/lib/scraper/extractor';
import { evaluateATS } from '@/lib/ai/ats-scorer';
import { evaluateJobBlocks } from '@/lib/ai/job-evaluator';
import { CVData } from '@/lib/document/docx-generator';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/ssr';
import { z } from 'zod';
import { validatePayloadSize, sanitizeText } from '@/lib/security/sanitizer';
import { auditLog } from '@/lib/security/audit-log';

// Misma lista que /api/apply -- mantener sincronizadas si cambia una.
const ALLOWED_DOMAINS = [
  'getonbrd.com',
  'linkedin.com',
  'indeed.com',
  'computrabajo.com',
  'laborum.cl',
  'trabajando.cl',
  'bne.cl',
  'chiletrabajos.cl',
];

function isAllowedUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ALLOWED_DOMAINS.some(domain => parsed.hostname.endsWith(domain));
  } catch {
    return false;
  }
}

const evaluateSchema = z.object({
  url: z.string().url("Debe ser una URL válida").max(500, "URL demasiado larga"),
  profile: z.record(z.string(), z.any()).refine(
    val => JSON.stringify(val).length < 50000,
    "El perfil es demasiado extenso"
  ),
});

function summarizeCv(profile: CVData): string {
  const parts: string[] = [];
  if (profile.summary) parts.push(profile.summary);
  if (profile.experience?.length) {
    parts.push('Experiencia: ' + profile.experience.map(e => `${e.position} en ${e.company}`).join('; '));
  }
  if (profile.skills?.length) parts.push('Skills: ' + profile.skills.join(', '));
  return parts.join('\n') || JSON.stringify(profile).slice(0, 2000);
}

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
      auditLog({ action: 'auth.unauthorized', path: '/api/evaluate', ip: req.headers.get('x-forwarded-for') ?? undefined });
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { data: creditProfile, error: creditError } = await supabase
      .from('profiles')
      .select('ai_credits_used, ai_credits_limit')
      .eq('id', user.id)
      .single();

    if (!creditError && creditProfile) {
      const used = creditProfile.ai_credits_used ?? 0;
      const limit = creditProfile.ai_credits_limit ?? 10;
      if (used >= limit) {
        auditLog({
          action: 'evaluate.blocked',
          userId: user.id,
          path: '/api/evaluate',
          details: { reason: 'ai_credits_limit alcanzado', used, limit },
        });
        return NextResponse.json(
          { error: `Alcanzaste el límite de ${limit} créditos de IA de tu plan. Mejora tu plan en Configuración para seguir evaluando ofertas.` },
          { status: 403 }
        );
      }
    }

    const json = await req.json();

    const sizeCheck = validatePayloadSize(json, 100_000);
    if (!sizeCheck.safe) {
      auditLog({ action: 'evaluate.blocked', userId: user.id, path: '/api/evaluate', details: { reason: sizeCheck.reason } });
      return NextResponse.json({ error: sizeCheck.reason }, { status: 413 });
    }

    const parsedData = evaluateSchema.safeParse(json);
    if (!parsedData.success) {
      return NextResponse.json({ error: 'Invalid input', details: parsedData.error.issues }, { status: 400 });
    }

    const { url, profile } = parsedData.data;

    if (!isAllowedUrl(url)) {
      auditLog({
        action: 'evaluate.blocked',
        userId: user.id,
        path: '/api/evaluate',
        details: { reason: 'URL de dominio no permitido', url },
      });
      return NextResponse.json(
        { error: 'Solo se permiten URLs de portales de empleo conocidos (LinkedIn, GetOnBrd, Indeed, etc.).' },
        { status: 400 }
      );
    }

    auditLog({ action: 'evaluate.request', userId: user.id, path: '/api/evaluate', details: { url } });

    // 1. Scrape
    const source = url.includes('getonbrd.com') ? 'GetOnBoard' : url.includes('linkedin.com') ? 'LinkedIn' : 'Other';
    const jobOffer = await scrapeJobOffer(url, source);

    // 2. Sanitizar la descripcion scrapeada antes de mandarla a la IA
    // (limpieza de caracteres invisibles/control -- sin el chequeo de
    // patrones de injection de sanitizeChatMessage, que da falsos positivos
    // con frases normales de una oferta como "actuar como punto de contacto").
    const cleanDescription = sanitizeText(jobOffer.rawDescription);
    if (cleanDescription.length < 100) {
      return NextResponse.json(
        { error: 'No se pudo extraer suficiente contenido de la oferta para evaluarla.' },
        { status: 422 }
      );
    }
    const sanitizedJobOffer = { ...jobOffer, rawDescription: cleanDescription };

    // 3. Las 2 llamadas de IA
    const cvSummary = summarizeCv(profile as CVData);
    const [cvMatch, blocks] = await Promise.all([
      evaluateATS(cvSummary, cleanDescription),
      evaluateJobBlocks(sanitizedJobOffer, cvSummary),
    ]);

    // 4. Score final ponderado (calculado en codigo, no por la IA)
    const cvMatchScore5 = 1.0 + (cvMatch.overallScore / 100) * 4.0;
    const rawScore =
      cvMatchScore5 * 0.30 +
      blocks.levelStrategy.score * 0.15 +
      blocks.salaryResearch.score * 0.15 +
      blocks.personalization.score * 0.15 +
      blocks.roleSummary.score * 0.15 +
      blocks.interviewPrep.score * 0.10;
    const overallScore = Math.round(rawScore * 10) / 10;

    // 5. Guardar + gastar 1 credito (una sola vez, aunque fueron 2 llamadas de IA)
    let evaluationId: string | null = null;
    try {
      const { data: inserted } = await supabase.from('job_evaluations').insert({
        user_id: user.id,
        job_url: url,
        company_name: jobOffer.company || 'Empresa',
        job_title: jobOffer.title || 'Cargo',
        jd_raw: cleanDescription,
        overall_score: overallScore,
        blocks: { ...blocks, cvMatch },
        is_suspicious: blocks.blockG.isSuspicious,
        suspicious_reason: blocks.blockG.reason,
      }).select('id').single();
      evaluationId = inserted?.id ?? null;

      const { data: prof } = await supabase.from('profiles').select('ai_credits_used').eq('id', user.id).single();
      if (prof) {
        await supabase.from('profiles').update({ ai_credits_used: (prof.ai_credits_used || 0) + 1 }).eq('id', user.id);
      }
    } catch (dbErr) {
      console.warn('[Evaluate API] Warning: Failed to insert DB records:', dbErr);
    }

    return NextResponse.json({
      success: true,
      evaluationId,
      overallScore,
      isSuspicious: blocks.blockG.isSuspicious,
      suspiciousReason: blocks.blockG.reason,
      blocks,
      cvMatch,
      jobOffer: { title: jobOffer.title, company: jobOffer.company },
    });

  } catch (error: unknown) {
    console.error('[Evaluate API] Error:', error);
    return NextResponse.json(
      { error: 'Failed to evaluate job offer', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 2: Add `/api/evaluate` to the AI rate-limit group**

In `src/middleware.ts`, find line 31:
```typescript
function isAiRoute(pathname: string): boolean {
  return pathname.startsWith('/api/chat') || pathname.startsWith('/api/apply') || pathname.startsWith('/api/cv/parse');
}
```
Replace with:
```typescript
function isAiRoute(pathname: string): boolean {
  return pathname.startsWith('/api/chat') || pathname.startsWith('/api/apply') || pathname.startsWith('/api/cv/parse') || pathname.startsWith('/api/evaluate');
}
```

- [ ] **Step 3: Verify it compiles**

Run: `cd /home/ale/Antigravity/huntjob-web/huntjob-web && npx tsc --noEmit`
Expected: no new type errors.

- [ ] **Step 4: Manual end-to-end test against the dev server**

```bash
cd /home/ale/Antigravity/huntjob-web/huntjob-web
npm run dev
```
In a browser logged into a real test account, open devtools console on any page of the app and run:
```javascript
fetch('/api/evaluate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://www.getonbrd.com/jobs/some-real-job-slug', // reemplazar con una oferta real vigente
    profile: { summary: 'Ingeniero de software con 5 años en backend', experience: [], education: [], skills: ['TypeScript', 'Node.js'], personalInfo: { name: 'Test', email: 'test@test.com', phone: '' } }
  })
}).then(r => r.json()).then(console.log)
```
Expected: JSON response with `success: true`, `overallScore` between 1.0 and 5.0, `blocks` with all 6 sub-objects, `cvMatch` with `overallScore` 0-100. Then in Supabase Table Editor, confirm a new row exists in `job_evaluations` and `profiles.ai_credits_used` incremented by exactly 1 (not 2).

- [ ] **Step 5: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web/huntjob-web
git add src/app/api/evaluate/route.ts src/middleware.ts
git commit -m "feat(api): agrega POST /api/evaluate con rate limit de IA"
```

---

### Task 4: Link `evaluation_id` from an evaluation into a real application

**Files:**
- Modify: `src/app/api/apply/route.ts:32-38` (schema), `:88-101` (parsing), `:134-142` (insert)

**Interfaces:**
- Consumes: nothing new from earlier tasks — this task only makes `/api/apply` accept an already-existing `evaluationId` string produced by Task 3's response.
- Produces: `applications` rows now optionally carry `evaluation_id` — no new interface for later tasks (Task 5 is the last consumer, calling this endpoint from the browser, not importing anything).

- [ ] **Step 1: Extend the request schema**

In `src/app/api/apply/route.ts`, find:
```typescript
const applySchema = z.object({
  url: z.string().url("Debe ser una URL válida").max(500, "URL demasiado larga"),
  profile: z.record(z.string(), z.any()).refine(
    val => JSON.stringify(val).length < 50000, 
    "El perfil es demasiado extenso"
  )
});
```
Replace with:
```typescript
const applySchema = z.object({
  url: z.string().url("Debe ser una URL válida").max(500, "URL demasiado larga"),
  profile: z.record(z.string(), z.any()).refine(
    val => JSON.stringify(val).length < 50000, 
    "El perfil es demasiado extenso"
  ),
  evaluationId: z.string().uuid().optional(),
});
```

- [ ] **Step 2: Pass it through and store it**

Find:
```typescript
    const { url, profile } = parsedData.data;
```
Replace with:
```typescript
    const { url, profile, evaluationId } = parsedData.data;
```

Find the `applications` insert:
```typescript
      await supabase.from('applications').insert({
        user_id: user.id,
        company_name: jobOffer.company || 'Empresa',
        job_title: jobOffer.title || 'Cargo Oportunidad',
        job_url: url,
        status: 'pending',
        adapted_cv: adaptedCv,
      });
```
Replace with:
```typescript
      await supabase.from('applications').insert({
        user_id: user.id,
        company_name: jobOffer.company || 'Empresa',
        job_title: jobOffer.title || 'Cargo Oportunidad',
        job_url: url,
        status: 'pending',
        adapted_cv: adaptedCv,
        evaluation_id: evaluationId ?? null,
      });
```

- [ ] **Step 3: Verify it compiles**

Run: `cd /home/ale/Antigravity/huntjob-web/huntjob-web && npx tsc --noEmit`
Expected: no new type errors.

- [ ] **Step 4: Manual test — apply without an evaluationId still works (backwards compatibility)**

```javascript
fetch('/api/apply', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: 'https://www.getonbrd.com/jobs/some-real-job-slug', profile: { summary: 'Test', experience: [], education: [], skills: [], personalInfo: { name: 'Test', email: 'test@test.com', phone: '' } } })
}).then(r => r.json()).then(console.log)
```
Expected: still succeeds exactly as before Task 4 (no `evaluationId` in the request body is valid, since the field is `.optional()`).

- [ ] **Step 5: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web/huntjob-web
git add src/app/api/apply/route.ts
git commit -m "feat(api): /api/apply acepta evaluationId opcional para linkear con job_evaluations"
```

---

### Task 5: `/dashboard/evaluate` — the UI

**Files:**
- Create: `src/app/dashboard/evaluate/page.tsx`

**Interfaces:**
- Consumes: `POST /api/evaluate` (Task 3's exact response shape), `POST /api/apply` (Task 4's extended body, passing `evaluationId`).

- [ ] **Step 1: Write the page**

```tsx
// src/app/dashboard/evaluate/page.tsx
"use client";

import { useState } from "react";
import { createClient } from "@/utils/supabase/client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Search } from "lucide-react";

interface InterviewQuestion {
  question: string;
  starHint: string;
}

interface EvaluateResponse {
  success: boolean;
  evaluationId: string | null;
  overallScore: number;
  isSuspicious: boolean;
  suspiciousReason: string | null;
  blocks: {
    roleSummary: { score: number; summary: string };
    levelStrategy: { score: number; fit: string; advice: string };
    salaryResearch: { score: number; estimatedRange: string; confidence: string };
    personalization: { score: number; angle: string };
    interviewPrep: { score: number; questions: InterviewQuestion[] };
  };
  jobOffer: { title: string; company: string };
  error?: string;
}

export default function EvaluatePage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<EvaluateResponse | null>(null);

  const supabase = createClient();

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data: resumes } = await supabase
        .from("resumes")
        .select("cv_data")
        .eq("user_id", user.id)
        .is("target_company", null)
        .order("created_at", { ascending: false })
        .limit(1);

      const profile = resumes?.[0]?.cv_data;
      if (!profile) {
        setError("Necesitas subir tu CV base antes de evaluar ofertas.");
        setLoading(false);
        return;
      }

      const res = await fetch("/api/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, profile }),
      });
      const json: EvaluateResponse = await res.json();
      if (!res.ok) {
        setError(json.error || "No se pudo evaluar la oferta.");
      } else {
        setReport(json);
      }
    } catch {
      setError("Error de red evaluando la oferta.");
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!report) return;
    setApplying(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;
      const { data: resumes } = await supabase
        .from("resumes")
        .select("cv_data")
        .eq("user_id", user.id)
        .is("target_company", null)
        .order("created_at", { ascending: false })
        .limit(1);
      const profile = resumes?.[0]?.cv_data;

      const res = await fetch("/api/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, profile, evaluationId: report.evaluationId }),
      });
      const json = await res.json();
      if (res.ok) {
        window.location.href = "/dashboard/applications";
      } else {
        setError(json.error || "No se pudo postular.");
      }
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      <div>
        <h1 className="text-3xl font-heading font-bold text-white tracking-tight">Evaluar Oferta</h1>
        <p className="text-zinc-400 mt-1">Pega la URL de una oferta y decide si vale la pena postular antes de gastar un crédito en aplicar.</p>
      </div>

      <Card className="bg-zinc-900/60 border-white/10 p-6">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              placeholder="https://www.getonbrd.com/jobs/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full bg-black/50 border border-white/10 rounded-lg py-2.5 pl-10 pr-4 text-sm text-white"
            />
          </div>
          <Button onClick={handleEvaluate} disabled={loading || !url} className="bg-indigo-600 hover:bg-indigo-500 text-white">
            {loading ? "Evaluando..." : "Evaluar"}
          </Button>
        </div>
        {error && <p className="text-sm text-rose-400 mt-3">{error}</p>}
      </Card>

      {report && (
        <div className="space-y-4">
          {report.isSuspicious && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-400">Esta oferta muestra señales de sospecha</p>
                <p className="text-sm text-zinc-400 mt-1">{report.suspiciousReason}</p>
              </div>
            </div>
          )}

          <Card className="bg-zinc-900/60 border-white/10 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white">{report.jobOffer.title}</h2>
                <p className="text-zinc-400">{report.jobOffer.company}</p>
              </div>
              <div className="text-right">
                <div className="text-4xl font-bold text-indigo-400">{report.overallScore.toFixed(1)}</div>
                <div className="text-xs text-zinc-500">de 5.0</div>
              </div>
            </div>
            <Button onClick={handleApply} disabled={applying} className="mt-4 bg-emerald-600 hover:bg-emerald-500 text-white w-full">
              {applying ? "Postulando..." : "Aplicar con CV tailorado para esta oferta"}
            </Button>
          </Card>

          <Card className="bg-zinc-900/40 border-white/10 p-6">
            <Badge variant="outline" className="mb-2">Resumen del rol · {report.blocks.roleSummary.score.toFixed(1)}</Badge>
            <p className="text-sm text-zinc-300">{report.blocks.roleSummary.summary}</p>
          </Card>

          <Card className="bg-zinc-900/40 border-white/10 p-6">
            <Badge variant="outline" className="mb-2">Estrategia de nivel · {report.blocks.levelStrategy.score.toFixed(1)}</Badge>
            <p className="text-sm text-zinc-500 mb-1">Nivel: {report.blocks.levelStrategy.fit}</p>
            <p className="text-sm text-zinc-300">{report.blocks.levelStrategy.advice}</p>
          </Card>

          <Card className="bg-zinc-900/40 border-white/10 p-6">
            <Badge variant="outline" className="mb-2">Investigación salarial · {report.blocks.salaryResearch.score.toFixed(1)}</Badge>
            <p className="text-sm text-zinc-300">{report.blocks.salaryResearch.estimatedRange}</p>
            <p className="text-xs text-zinc-500 mt-1">Confianza de la estimación: {report.blocks.salaryResearch.confidence}</p>
          </Card>

          <Card className="bg-zinc-900/40 border-white/10 p-6">
            <Badge variant="outline" className="mb-2">Personalización · {report.blocks.personalization.score.toFixed(1)}</Badge>
            <p className="text-sm text-zinc-300">{report.blocks.personalization.angle}</p>
          </Card>

          <Card className="bg-zinc-900/40 border-white/10 p-6">
            <Badge variant="outline" className="mb-2">Prep de entrevista · {report.blocks.interviewPrep.score.toFixed(1)}</Badge>
            <div className="space-y-3">
              {report.blocks.interviewPrep.questions.map((q, i) => (
                <div key={i}>
                  <p className="text-sm text-zinc-200 font-medium">{q.question}</p>
                  <p className="text-sm text-zinc-500">{q.starHint}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify it compiles**

Run: `cd /home/ale/Antigravity/huntjob-web/huntjob-web && npx tsc --noEmit`
Expected: no new type errors.

- [ ] **Step 3: Manual browser test**

```bash
npm run dev
```
Open `http://localhost:3000/dashboard/evaluate` logged in as a real test user with a base CV already uploaded. Paste a real job URL from an allowed domain, click "Evaluar". Expected: loading state, then the full report renders (score, all 5 text blocks, Block G banner only if flagged). Click "Aplicar con CV tailorado para esta oferta" and confirm it redirects to `/dashboard/applications` and the new application appears there.

- [ ] **Step 4: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web/huntjob-web
git add src/app/dashboard/evaluate/page.tsx
git commit -m "feat(ui): agrega pantalla /dashboard/evaluate"
```

---

### Task 6: Whole-feature smoke test and push

**Files:** none (verification only)

- [ ] **Step 1: Full flow test**

With the dev server running and logged in as a real test account:
1. Go to `/dashboard/evaluate`, evaluate a real job offer.
2. Confirm `ai_credits_used` went up by exactly 1 in Supabase.
3. Confirm a row exists in `job_evaluations` with all 7 blocks (6 + cvMatch) in the `blocks` JSONB column.
4. Click apply from the report; confirm the new `applications` row has `evaluation_id` matching the `job_evaluations.id` from step 3.
5. Evaluate a second, different offer without applying — confirm `applications` is untouched (no orphan row) and a second `job_evaluations` row exists.

- [ ] **Step 2: Push**

```bash
cd /home/ale/Antigravity/huntjob-web/huntjob-web
git push origin main
```
