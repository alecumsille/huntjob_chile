# Datos reales en dashboard, apply y postulaciones — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every hardcoded/fake value in HuntJob Web's dashboard (activity feed, stats grid, apply-with-AI profile) and the postulaciones page (mock fallback) with real data from Supabase, and let a first-time user reach their first real application by capturing a base CV (PDF upload + AI extraction, editable) instead of relying on a fixed mock profile.

**Architecture:** No schema changes. The user's most recent row in `resumes` (already `CVData`-shaped JSONB) doubles as their "base CV" for the next apply. A new `POST /api/cv/parse` endpoint turns an uploaded PDF into that same `CVData` shape via the AI SDK's multimodal file input, reusing the existing `executeWithFallback` provider strategy. All reads/writes go through the already-authenticated Supabase client patterns already used elsewhere in this codebase (`src/utils/supabase/client.ts` client-side, `src/utils/supabase/server.ts` server-side).

**Tech Stack:** Next.js 15 App Router, TypeScript, Supabase (`@supabase/ssr`), Vercel AI SDK (`ai`, `@ai-sdk/openai`, `@ai-sdk/google`), zod, Tailwind + shadcn-style components already in `src/components/ui/`.

## Global Constraints

- No new npm dependencies. PDF text extraction uses the AI SDK's native multimodal file input (no PDF-parsing library); relative time uses a hand-written helper (no date library); the CV capture flow is inline in the page (no Dialog/modal library).
- No test framework is added. This repo has none (`package.json` has no `jest`/`vitest`) and the approved spec explicitly chose manual browser verification over adding one. Verification per task is either (a) the project's own `npx tsc --noEmit` for type correctness, (b) a throwaway Node script for pure logic (Node 22 in this environment runs `.ts` files with explicit extensions natively — verified working during planning), or (c) manual browser steps for anything touching auth/Supabase/UI.
- `POST /api/cv/parse` does **not** decrement `profiles.ai_credits_used` — it's one-time onboarding, not a job application.
- Every new/modified API route keeps the existing auth pattern: real Supabase server client, explicit `401` if `supabase.auth.getUser()` returns no user (same as `src/app/api/apply/route.ts`).
- AI-extracted free-text fields (`summary`, `achievements`) are checked with the existing `detectPromptInjection` from `src/lib/security/sanitizer.ts` before being returned to the client — reusing the existing mechanism, not building a new one.
- PDF upload capped at **4MB** (not 5MB as in the spec draft) — Vercel serverless functions cap request bodies around 4.5MB total including multipart overhead; 4MB of PDF stays safely under that with headroom.
- Never silently substitute fake/mock data for a failed or empty query. Every list/stat either shows real data, a real loading state, a real empty state, or a real error state.
- Two dashboard stats (`Vistas de Reclutadores`, `Score ATS Promedio`) have no real data source today and are **removed**, not faked — per spec addendum, confirmed with Alejandro.

---

### Task 1: Extract the shared CV zod schema

**Files:**
- Create: `src/lib/ai/cv-schema.ts`
- Modify: `src/lib/ai/cv-adapter.ts:1-30`

**Interfaces:**
- Produces: `CVSchema` (zod object) — used by Task 3's new parse route and by the existing `adaptCvToJob` in `cv-adapter.ts`.

- [ ] **Step 1: Create the shared schema file**

`src/lib/ai/cv-schema.ts`:

```ts
import { z } from 'zod';

export const CVSchema = z.object({
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
```

- [ ] **Step 2: Point `cv-adapter.ts` at the shared schema**

In `src/lib/ai/cv-adapter.ts`, replace lines 1-30 (the imports plus the inline `CVSchema` block) with:

```ts
import { generateObject } from 'ai';
import { executeWithFallback } from './provider';
import { type JobOffer } from '../scraper/schema';
import { type CVData } from '../document/docx-generator';
import { CVSchema } from './cv-schema';
```

Leave the rest of the file (the `adaptCvToJob` function body) untouched — it already references `CVSchema` and `CVData` by name, which still resolve correctly.

- [ ] **Step 3: Verify with the project's own type checker**

Run: `cd /home/ale/Antigravity/huntjob-web/huntjob-web && npx tsc --noEmit`
Expected: no errors mentioning `cv-adapter.ts` or `cv-schema.ts`.

- [ ] **Step 4: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web
git add huntjob-web/src/lib/ai/cv-schema.ts huntjob-web/src/lib/ai/cv-adapter.ts
git commit -m "refactor: extract shared CVSchema out of cv-adapter.ts

Needed by the new /api/cv/parse endpoint (Task 3) so both the CV
adapter and the CV parser validate against the exact same shape."
```

---

### Task 2: Relative-time helper

**Files:**
- Create: `src/lib/utils/time.ts`

**Interfaces:**
- Produces: `formatRelativeTime(dateString: string): string` — consumed by Task 5's dashboard activity feed.

- [ ] **Step 1: Write the helper**

`src/lib/utils/time.ts`:

```ts
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'Justo ahora';
  if (diffMin < 60) return `Hace ${diffMin} ${diffMin === 1 ? 'minuto' : 'minutos'}`;
  if (diffHour < 24) return `Hace ${diffHour} ${diffHour === 1 ? 'hora' : 'horas'}`;
  if (diffDay === 1) return 'Ayer';
  if (diffDay < 7) return `Hace ${diffDay} días`;
  return date.toLocaleDateString('es-CL', { day: 'numeric', month: 'short' });
}
```

- [ ] **Step 2: Write and run a throwaway verification script**

Create `/tmp/verify-time.mjs` (this is scratch — not committed):

```js
import { formatRelativeTime } from '/home/ale/Antigravity/huntjob-web/huntjob-web/src/lib/utils/time.ts';

const now = new Date();
const minutesAgo = (n) => new Date(now.getTime() - n * 60_000).toISOString();
const hoursAgo = (n) => new Date(now.getTime() - n * 3_600_000).toISOString();
const daysAgo = (n) => new Date(now.getTime() - n * 86_400_000).toISOString();

const cases = [
  [minutesAgo(0.5), 'Justo ahora'],
  [minutesAgo(5), 'Hace 5 minutos'],
  [hoursAgo(2), 'Hace 2 horas'],
  [daysAgo(1), 'Ayer'],
  [daysAgo(3), 'Hace 3 días'],
];

let allPass = true;
for (const [input, expected] of cases) {
  const actual = formatRelativeTime(input);
  const pass = actual === expected;
  if (!pass) allPass = false;
  console.log(`${pass ? 'PASS' : 'FAIL'}: formatRelativeTime(${input}) = "${actual}" (expected "${expected}")`);
}
console.log(allPass ? '\nALL PASS' : '\nSOME FAILED');
```

Run: `node /tmp/verify-time.mjs`
Expected: `ALL PASS` (Node 22 in this environment natively runs `.ts` files referenced with an explicit `.ts` extension — no build step needed).

- [ ] **Step 3: Delete the throwaway script**

Run: `rm /tmp/verify-time.mjs`

- [ ] **Step 4: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web
git add huntjob-web/src/lib/utils/time.ts
git commit -m "feat: add formatRelativeTime helper for real activity timestamps"
```

---

### Task 3: `POST /api/cv/parse` endpoint

**Files:**
- Create: `src/app/api/cv/parse/route.ts`
- Modify: `src/middleware.ts:30-32`

**Interfaces:**
- Consumes: `CVSchema` from `src/lib/ai/cv-schema.ts` (Task 1), `executeWithFallback` from `src/lib/ai/provider.ts` (existing), `createClient` from `src/utils/supabase/server.ts` (existing), `detectPromptInjection` and `auditLog` (existing).
- Produces: `POST /api/cv/parse` — accepts `multipart/form-data` with a `file` field (PDF), returns `{ success: true, cvData: CVData }` on `200`, or `{ error: string }` on `400`/`401`/`413`/`422`/`500`. Consumed by Task 4's `CvCaptureForm`.

- [ ] **Step 1: Write the route**

`src/app/api/cv/parse/route.ts`:

```ts
import { NextResponse } from 'next/server';
import { generateObject } from 'ai';
import { executeWithFallback } from '@/lib/ai/provider';
import { CVSchema } from '@/lib/ai/cv-schema';
import { createClient } from '@/utils/supabase/server';
import { auditLog } from '@/lib/security/audit-log';
import { detectPromptInjection } from '@/lib/security/sanitizer';

const MAX_PDF_BYTES = 4 * 1024 * 1024; // 4MB — Vercel functions cap request bodies around 4.5MB total

const EXTRACTION_PROMPT = `
Eres un extractor de datos de CVs. Analiza el PDF adjunto y devuelve la información
estructurada exactamente en el esquema JSON indicado.

REGLAS:
1. Si un campo no aparece en el PDF, usa un string vacío ("") o un array vacío ([]), nunca inventes datos.
2. Fechas en el formato que aparezcan en el original (ej. "Ene 2021", "2021", "Presente").
3. "achievements" son las viñetas/logros bajo cada experiencia laboral, tal como aparecen (no las reescribas).
4. No agregues comentarios ni texto fuera del JSON del esquema.
`;

export async function POST(req: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    auditLog({ action: 'auth.unauthorized', path: '/api/cv/parse', ip: req.headers.get('x-forwarded-for') ?? undefined });
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const formData = await req.formData();
  const file = formData.get('file');

  if (!(file instanceof File)) {
    return NextResponse.json({ error: 'Falta el archivo PDF.' }, { status: 400 });
  }

  if (file.type !== 'application/pdf') {
    return NextResponse.json({ error: 'Solo se aceptan archivos PDF.' }, { status: 400 });
  }

  if (file.size > MAX_PDF_BYTES) {
    return NextResponse.json({ error: 'El PDF supera el límite de 4MB.' }, { status: 413 });
  }

  auditLog({ action: 'apply.request', userId: user.id, path: '/api/cv/parse', details: { filename: file.name } });

  try {
    const pdfBuffer = Buffer.from(await file.arrayBuffer());

    const result = await executeWithFallback((model) =>
      generateObject({
        model,
        schema: CVSchema,
        messages: [
          {
            role: 'user',
            content: [
              { type: 'text', text: EXTRACTION_PROMPT },
              { type: 'file', data: pdfBuffer, mediaType: 'application/pdf' },
            ],
          },
        ],
      })
    );

    const cvData = result.object;

    const freeTextFields = [cvData.summary, ...cvData.experience.flatMap((e) => e.achievements)];
    for (const text of freeTextFields) {
      if (!text) continue;
      const check = detectPromptInjection(text);
      if (!check.safe) {
        auditLog({ action: 'injection.detected', userId: user.id, path: '/api/cv/parse' });
        return NextResponse.json(
          { error: 'El PDF contiene texto que no pudimos procesar de forma segura. Completa el formulario manualmente.' },
          { status: 422 }
        );
      }
    }

    return NextResponse.json({ success: true, cvData });
  } catch (error: unknown) {
    console.error('[CV Parse] Error:', error);
    return NextResponse.json(
      { error: 'No pudimos leer tu PDF. Completa el formulario manualmente.' },
      { status: 422 }
    );
  }
}
```

- [ ] **Step 2: Add the route to the AI rate-limit bucket**

In `src/middleware.ts`, find:

```ts
function isAiRoute(pathname: string): boolean {
  return pathname.startsWith('/api/chat') || pathname.startsWith('/api/apply');
}
```

Replace with:

```ts
function isAiRoute(pathname: string): boolean {
  return pathname.startsWith('/api/chat') || pathname.startsWith('/api/apply') || pathname.startsWith('/api/cv/parse');
}
```

- [ ] **Step 3: Verify types**

Run: `cd /home/ale/Antigravity/huntjob-web/huntjob-web && npx tsc --noEmit`
Expected: no errors mentioning `src/app/api/cv/parse/route.ts` or `src/middleware.ts`.

- [ ] **Step 4: Manual verification against the real dev server**

Run: `npm run dev` (from `/home/ale/Antigravity/huntjob-web/huntjob-web`), then in a second terminal, while logged out:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:3000/api/cv/parse
```

Expected: `401`.

Then log in via the browser at `http://localhost:3000/auth/login`, copy the `sb-*-auth-token` cookie from devtools, and:

```bash
curl -s -X POST http://localhost:3000/api/cv/parse \
  -H "Cookie: <pega aquí la cookie completa>" \
  -F "file=@/path/a/un/cv/real.pdf" | head -c 500
```

Expected: `{"success":true,"cvData":{"personalInfo":{...`. Confirm the extracted name/email/experience roughly match the real PDF.

- [ ] **Step 5: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web
git add huntjob-web/src/app/api/cv/parse/route.ts huntjob-web/src/middleware.ts
git commit -m "feat: add POST /api/cv/parse to extract CVData from an uploaded PDF

Reuses executeWithFallback (OpenAI primary, Gemini fallback) with
native multimodal file input — no PDF-parsing library needed."
```

---

### Task 4: `CvCaptureForm` component

**Files:**
- Create: `src/components/cv/CvCaptureForm.tsx`

**Interfaces:**
- Consumes: `POST /api/cv/parse` (Task 3), `CVData` type from `src/lib/document/docx-generator.ts` (existing), UI primitives from `src/components/ui/{button,input,label,textarea,card}.tsx` (existing).
- Produces: `<CvCaptureForm onComplete={(cvData: CVData) => void} onCancel={() => void} />` — consumed by Task 5's `dashboard/page.tsx`.

- [ ] **Step 1: Write the component**

`src/components/cv/CvCaptureForm.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Loader2, Plus, Trash2, UploadCloud, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import type { CVData } from "@/lib/document/docx-generator";

interface CvCaptureFormProps {
  onComplete: (cvData: CVData) => void;
  onCancel: () => void;
}

const EMPTY_CV: CVData = {
  personalInfo: { name: "", email: "", phone: "", linkedin: "", location: "" },
  summary: "",
  experience: [],
  education: [],
  skills: [],
};

export function CvCaptureForm({ onComplete, onCancel }: CvCaptureFormProps) {
  const [step, setStep] = useState<"upload" | "edit">("upload");
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState("");
  const [cv, setCv] = useState<CVData>(EMPTY_CV);
  const [skillsText, setSkillsText] = useState("");
  const [formError, setFormError] = useState("");

  const handleFileUpload = async (file: globalThis.File) => {
    setParsing(true);
    setParseError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/cv/parse", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) {
        setParseError(data.error || "No pudimos leer tu PDF.");
        setCv(EMPTY_CV);
        setSkillsText("");
      } else {
        setCv(data.cvData as CVData);
        setSkillsText(((data.cvData as CVData).skills || []).join(", "));
      }
    } catch {
      setParseError("No pudimos leer tu PDF.");
      setCv(EMPTY_CV);
      setSkillsText("");
    } finally {
      setParsing(false);
      setStep("edit");
    }
  };

  const handleSkipUpload = () => {
    setCv(EMPTY_CV);
    setSkillsText("");
    setStep("edit");
  };

  const updatePersonalInfo = (field: keyof CVData["personalInfo"], value: string) => {
    setCv((prev) => ({ ...prev, personalInfo: { ...prev.personalInfo, [field]: value } }));
  };

  const addExperience = () => {
    setCv((prev) => ({
      ...prev,
      experience: [...prev.experience, { company: "", position: "", startDate: "", endDate: "", achievements: [""] }],
    }));
  };

  const updateExperience = (
    index: number,
    field: "company" | "position" | "startDate" | "endDate",
    value: string
  ) => {
    setCv((prev) => ({
      ...prev,
      experience: prev.experience.map((exp, i) => (i === index ? { ...exp, [field]: value } : exp)),
    }));
  };

  const updateAchievement = (expIndex: number, achIndex: number, value: string) => {
    setCv((prev) => ({
      ...prev,
      experience: prev.experience.map((exp, i) =>
        i === expIndex
          ? { ...exp, achievements: exp.achievements.map((a, j) => (j === achIndex ? value : a)) }
          : exp
      ),
    }));
  };

  const addAchievement = (expIndex: number) => {
    setCv((prev) => ({
      ...prev,
      experience: prev.experience.map((exp, i) =>
        i === expIndex ? { ...exp, achievements: [...exp.achievements, ""] } : exp
      ),
    }));
  };

  const removeExperience = (index: number) => {
    setCv((prev) => ({ ...prev, experience: prev.experience.filter((_, i) => i !== index) }));
  };

  const addEducation = () => {
    setCv((prev) => ({
      ...prev,
      education: [...prev.education, { institution: "", degree: "", graduationDate: "" }],
    }));
  };

  const updateEducation = (
    index: number,
    field: "institution" | "degree" | "graduationDate",
    value: string
  ) => {
    setCv((prev) => ({
      ...prev,
      education: prev.education.map((edu, i) => (i === index ? { ...edu, [field]: value } : edu)),
    }));
  };

  const removeEducation = (index: number) => {
    setCv((prev) => ({ ...prev, education: prev.education.filter((_, i) => i !== index) }));
  };

  const handleSubmit = () => {
    if (!cv.personalInfo.name.trim() || !cv.personalInfo.email.trim()) {
      setFormError("Nombre y email son obligatorios.");
      return;
    }
    setFormError("");
    const skills = skillsText.split(",").map((s) => s.trim()).filter(Boolean);
    onComplete({ ...cv, skills });
  };

  if (step === "upload") {
    return (
      <Card className="bg-zinc-900/60 border-white/10">
        <CardHeader>
          <CardTitle className="text-white">Completa tu CV base</CardTitle>
          <CardDescription>
            Es tu primera postulación — sube tu CV en PDF y la IA lo va a leer, o complétalo a mano.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {parseError && (
            <p className="text-sm text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
              {parseError}
            </p>
          )}
          <label className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-white/10 rounded-xl p-8 cursor-pointer hover:border-indigo-500/50 transition-colors">
            {parsing ? (
              <>
                <Loader2 className="h-8 w-8 text-indigo-400 animate-spin" />
                <span className="text-sm text-zinc-400">Analizando tu CV con IA...</span>
              </>
            ) : (
              <>
                <UploadCloud className="h-8 w-8 text-zinc-500" />
                <span className="text-sm text-zinc-400">Haz clic para subir tu CV (PDF, máx. 4MB)</span>
              </>
            )}
            <input
              type="file"
              accept="application/pdf"
              className="hidden"
              disabled={parsing}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileUpload(file);
              }}
            />
          </label>
          <div className="flex justify-between items-center">
            <Button variant="ghost" onClick={onCancel} disabled={parsing}>
              Cancelar
            </Button>
            <Button variant="outline" onClick={handleSkipUpload} disabled={parsing}>
              <FileText className="mr-2 h-4 w-4" /> Completar a mano
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-zinc-900/60 border-white/10">
      <CardHeader>
        <CardTitle className="text-white">Revisa y confirma tu CV base</CardTitle>
        <CardDescription>
          Corrige lo que necesites. Esto se guarda como tu CV base para futuras postulaciones.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {formError && <p className="text-sm text-rose-400">{formError}</p>}

        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Nombre completo</Label>
            <Input value={cv.personalInfo.name} onChange={(e) => updatePersonalInfo("name", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Email</Label>
            <Input value={cv.personalInfo.email} onChange={(e) => updatePersonalInfo("email", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Teléfono</Label>
            <Input value={cv.personalInfo.phone} onChange={(e) => updatePersonalInfo("phone", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>LinkedIn</Label>
            <Input value={cv.personalInfo.linkedin} onChange={(e) => updatePersonalInfo("linkedin", e.target.value)} />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label>Ubicación</Label>
            <Input value={cv.personalInfo.location} onChange={(e) => updatePersonalInfo("location", e.target.value)} />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Resumen profesional</Label>
          <Textarea
            value={cv.summary}
            onChange={(e) => setCv((prev) => ({ ...prev, summary: e.target.value }))}
            rows={3}
          />
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Experiencia</Label>
            <Button type="button" variant="outline" size="sm" onClick={addExperience}>
              <Plus className="h-4 w-4 mr-1" /> Agregar
            </Button>
          </div>
          {cv.experience.map((exp, i) => (
            <div key={i} className="border border-white/10 rounded-xl p-4 space-y-3">
              <div className="flex justify-end">
                <button type="button" onClick={() => removeExperience(i)} className="text-zinc-500 hover:text-rose-400">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="grid sm:grid-cols-2 gap-3">
                <Input placeholder="Empresa" value={exp.company} onChange={(e) => updateExperience(i, "company", e.target.value)} />
                <Input placeholder="Cargo" value={exp.position} onChange={(e) => updateExperience(i, "position", e.target.value)} />
                <Input placeholder="Inicio (ej. Ene 2021)" value={exp.startDate} onChange={(e) => updateExperience(i, "startDate", e.target.value)} />
                <Input placeholder="Fin (ej. Presente)" value={exp.endDate} onChange={(e) => updateExperience(i, "endDate", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Logros</Label>
                {exp.achievements.map((ach, j) => (
                  <Input
                    key={j}
                    placeholder="Ej. Lideré la migración a Next.js reduciendo el TTI en 40%"
                    value={ach}
                    onChange={(e) => updateAchievement(i, j, e.target.value)}
                  />
                ))}
                <Button type="button" variant="ghost" size="sm" onClick={() => addAchievement(i)}>
                  <Plus className="h-3 w-3 mr-1" /> Agregar logro
                </Button>
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Educación</Label>
            <Button type="button" variant="outline" size="sm" onClick={addEducation}>
              <Plus className="h-4 w-4 mr-1" /> Agregar
            </Button>
          </div>
          {cv.education.map((edu, i) => (
            <div key={i} className="border border-white/10 rounded-xl p-4 space-y-3">
              <div className="flex justify-end">
                <button type="button" onClick={() => removeEducation(i)} className="text-zinc-500 hover:text-rose-400">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="grid sm:grid-cols-3 gap-3">
                <Input placeholder="Institución" value={edu.institution} onChange={(e) => updateEducation(i, "institution", e.target.value)} />
                <Input placeholder="Título" value={edu.degree} onChange={(e) => updateEducation(i, "degree", e.target.value)} />
                <Input placeholder="Año" value={edu.graduationDate} onChange={(e) => updateEducation(i, "graduationDate", e.target.value)} />
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <Label>Skills (separadas por coma)</Label>
          <Input value={skillsText} onChange={(e) => setSkillsText(e.target.value)} placeholder="React, TypeScript, Node.js" />
        </div>

        <div className="flex justify-between items-center pt-2">
          <Button variant="ghost" onClick={onCancel}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit}>Guardar y continuar</Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Verify types**

Run: `cd /home/ale/Antigravity/huntjob-web/huntjob-web && npx tsc --noEmit`
Expected: no errors mentioning `CvCaptureForm.tsx`.

- [ ] **Step 3: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web
git add huntjob-web/src/components/cv/CvCaptureForm.tsx
git commit -m "feat: add CvCaptureForm — PDF upload + AI extraction + editable review"
```

---

### Task 5: Wire `dashboard/page.tsx` to real data

**Files:**
- Modify: `src/app/dashboard/page.tsx` (full rewrite of the file — see below)

**Interfaces:**
- Consumes: `createClient` from `src/utils/supabase/client.ts` (existing), `formatRelativeTime` from `src/lib/utils/time.ts` (Task 2), `CvCaptureForm` from `src/components/cv/CvCaptureForm.tsx` (Task 4), `type CVData` from `src/lib/document/docx-generator.ts` (existing), `POST /api/apply` (existing, unchanged contract).

- [ ] **Step 1: Replace the file**

Write the complete new `src/app/dashboard/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  CheckCircle2,
  Clock,
  Briefcase,
  Link as LinkIcon,
  Loader2,
  Download
} from "lucide-react";
import { createClient } from "@/utils/supabase/client";
import { formatRelativeTime } from "@/lib/utils/time";
import { CvCaptureForm } from "@/components/cv/CvCaptureForm";
import type { CVData } from "@/lib/document/docx-generator";

type ApplicationStatus = "pending" | "interview_scheduled" | "rejected" | "offer";

interface ApplicationRow {
  id: string;
  company_name: string;
  job_title: string;
  status: ApplicationStatus;
  applied_at: string;
}

interface Activity {
  role: string;
  company: string;
  status: string;
  time: string;
  color: string;
  bg: string;
}

const STATUS_META: Record<ApplicationStatus, { label: string; color: string; bg: string }> = {
  pending: { label: "En revisión", color: "text-amber-400", bg: "bg-amber-500/10" },
  interview_scheduled: { label: "Entrevista Agendada", color: "text-indigo-400", bg: "bg-indigo-500/10" },
  rejected: { label: "Rechazado", color: "text-rose-400", bg: "bg-rose-500/10" },
  offer: { label: "Oferta", color: "text-emerald-400", bg: "bg-emerald-500/10" },
};

function toActivity(row: ApplicationRow): Activity {
  const meta = STATUS_META[row.status];
  return {
    role: row.job_title,
    company: row.company_name,
    status: meta.label,
    time: formatRelativeTime(row.applied_at),
    color: meta.color,
    bg: meta.bg,
  };
}

export default function DashboardPage() {
  const supabase = createClient();

  const [url, setUrl] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [workflowStatus, setWorkflowStatus] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [showCapture, setShowCapture] = useState(false);

  const [activities, setActivities] = useState<Activity[]>([]);
  const [activitiesLoading, setActivitiesLoading] = useState(true);
  const [statsData, setStatsData] = useState({ totalApplications: 0, interviewsScheduled: 0 });

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  useEffect(() => {
    async function loadDashboardData() {
      setActivitiesLoading(true);
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        setActivitiesLoading(false);
        return;
      }

      const [recentRes, allRes] = await Promise.all([
        supabase
          .from("applications")
          .select("id, company_name, job_title, status, applied_at")
          .eq("user_id", user.id)
          .order("applied_at", { ascending: false })
          .limit(4),
        supabase
          .from("applications")
          .select("status")
          .eq("user_id", user.id),
      ]);

      if (!recentRes.error && recentRes.data) {
        setActivities((recentRes.data as ApplicationRow[]).map(toActivity));
      }

      if (!allRes.error && allRes.data) {
        const rows = allRes.data as { status: ApplicationStatus }[];
        setStatsData({
          totalApplications: rows.length,
          interviewsScheduled: rows.filter((r) => r.status === "interview_scheduled").length,
        });
      }

      setActivitiesLoading(false);
    }
    loadDashboardData();
  }, [supabase]);

  const runApply = async (profile: CVData) => {
    setIsProcessing(true);
    setResult(null);
    setWorkflowStatus("1/3: Iniciando scraper para leer la oferta...");

    try {
      setWorkflowStatus("2/3: Oferta leída. IA adaptando el CV...");
      const res = await fetch('/api/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, profile })
      });

      if (!res.ok) throw new Error("Error en la orquestación");

      const data = await res.json();
      setWorkflowStatus("3/3: ¡CV Optimizado con éxito!");
      setResult(data);

      setActivities(prev => [
        {
          role: data.jobOffer.title || "Nuevo Rol",
          company: data.jobOffer.company || "Nueva Empresa",
          status: STATUS_META.pending.label,
          time: "Justo ahora",
          color: STATUS_META.pending.color,
          bg: STATUS_META.pending.bg,
        },
        ...prev
      ].slice(0, 4));
      setStatsData((prev) => ({ ...prev, totalApplications: prev.totalApplications + 1 }));
    } catch (e) {
      console.error(e);
      setWorkflowStatus("Error al procesar la oferta.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApply = async () => {
    if (!url) return;
    setIsProcessing(true);

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      setIsProcessing(false);
      return;
    }

    const { data: resumes } = await supabase
      .from("resumes")
      .select("cv_data")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false })
      .limit(1);

    if (resumes && resumes.length > 0) {
      await runApply(resumes[0].cv_data as CVData);
    } else {
      setIsProcessing(false);
      setShowCapture(true);
    }
  };

  const handleCaptureComplete = async (cvData: CVData) => {
    setShowCapture(false);
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    await supabase.from("resumes").insert({
      user_id: user.id,
      name: "Mi CV Base",
      cv_data: cvData,
    });

    await runApply(cvData);
  };

  const handleCaptureCancel = () => {
    setShowCapture(false);
  };

  const handleDownloadDocx = async () => {
    if (!result?.adaptedCv) return;
    try {
      const res = await fetch('/api/export/docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result.adaptedCv)
      });
      if (!res.ok) throw new Error("Error en descarga");

      const blob = await res.blob();
      const objUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objUrl;
      a.download = `CV_Optimizado_${(result as { jobOffer: { company: string } }).jobOffer.company.replace(/ /g, '_')}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(objUrl);
    } catch (err) {
      console.error(err);
      alert("Error descargando el DOCX");
    }
  };

  const stats = [
    {
      title: "Postulaciones Automáticas",
      value: String(statsData.totalApplications),
      icon: Send,
      color: "text-indigo-400",
      bg: "bg-indigo-500/10",
      border: "border-indigo-500/20"
    },
    {
      title: "Entrevistas Agendadas",
      value: String(statsData.interviewsScheduled),
      icon: CheckCircle2,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      border: "border-purple-500/20"
    }
  ];

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <motion.div variants={itemVariants}>
          <h1 className="text-3xl font-heading font-bold text-white mb-2">Tu Panel de Impacto</h1>
          <p className="text-zinc-400">Automatiza tu búsqueda de empleo con el motor de Inteligencia Artificial.</p>
        </motion.div>
      </div>

      <motion.div variants={itemVariants}>
        {showCapture ? (
          <CvCaptureForm onComplete={handleCaptureComplete} onCancel={handleCaptureCancel} />
        ) : (
          <div className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-2xl p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/20 blur-[80px] -mr-32 -mt-32 pointer-events-none" />

            <div className="relative z-10 max-w-3xl">
              <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <Send className="h-5 w-5 text-indigo-400" />
                Nueva Postulación Automática
              </h2>
              <p className="text-sm text-zinc-400 mb-6">Pega el enlace de la oferta de trabajo (LinkedIn, GetOnBoard, etc.). La IA extraerá los datos, adaptará tu CV y te dará el documento listo para enviar.</p>

              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <LinkIcon className="h-5 w-5 text-zinc-500" />
                  </div>
                  <input
                    type="text"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={isProcessing}
                    placeholder="https://www.getonbrd.com/empleos/..."
                    className="w-full pl-10 pr-4 py-3 bg-zinc-900/50 border border-white/10 rounded-xl text-white placeholder:text-zinc-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all disabled:opacity-50"
                  />
                </div>
                <button
                  onClick={handleApply}
                  disabled={!url || isProcessing}
                  className="px-6 py-3 bg-indigo-500 hover:bg-indigo-600 text-white font-bold rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Adaptando...
                    </>
                  ) : (
                    <>Generar CV</>
                  )}
                </button>
              </div>

              <AnimatePresence>
                {workflowStatus && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-4 text-sm font-medium text-indigo-300 flex items-center gap-2"
                  >
                    {isProcessing && <Loader2 className="h-4 w-4 animate-spin" />}
                    {workflowStatus}
                  </motion.div>
                )}

                {result && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-6 p-5 bg-white/5 border border-white/10 rounded-xl"
                  >
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                      <div>
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                          <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                          CV Generado Exitosamente
                        </h3>
                        <p className="text-sm text-zinc-400 mt-1">
                          Adaptado para el rol de <strong className="text-white">{(result as { jobOffer: { title: string } }).jobOffer.title}</strong> en <strong className="text-white">{(result as { jobOffer: { company: string } }).jobOffer.company}</strong>
                        </p>
                      </div>

                      <button
                        onClick={handleDownloadDocx}
                        className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-lg transition-colors flex items-center gap-2 flex-shrink-0"
                      >
                        <Download className="h-4 w-4" />
                        Descargar Word (.docx)
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        )}
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {stats.map((stat, i) => (
          <motion.div
            key={i}
            variants={itemVariants}
            className="bg-zinc-900/50 border border-white/10 rounded-2xl p-6 backdrop-blur-sm relative overflow-hidden group"
          >
            <div className={`absolute top-0 right-0 w-32 h-32 ${stat.bg} blur-[50px] -mr-16 -mt-16 transition-opacity opacity-50 group-hover:opacity-100`} />
            <div className="flex justify-between items-start mb-6 relative z-10">
              <div className={`p-3 rounded-xl ${stat.bg} ${stat.border} border`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </div>
            <div className="relative z-10">
              <h3 className="text-3xl font-heading font-bold text-white mb-1">{stat.value}</h3>
              <p className="text-sm text-zinc-400 font-medium">{stat.title}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div variants={itemVariants} className="bg-zinc-900/50 border border-white/10 rounded-2xl backdrop-blur-sm overflow-hidden">
        <div className="p-6 border-b border-white/10 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">Actividad Reciente</h2>
        </div>

        {activitiesLoading ? (
          <div className="p-12 flex justify-center">
            <Loader2 className="h-6 w-6 text-zinc-500 animate-spin" />
          </div>
        ) : activities.length === 0 ? (
          <div className="p-12 text-center">
            <Briefcase className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
            <p className="text-zinc-400 text-sm">Aún no tienes postulaciones — pega una URL arriba para empezar.</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {activities.map((activity, i) => (
              <div key={i} className="p-4 sm:p-6 flex items-center gap-4 sm:gap-6 hover:bg-white/[0.02] transition-colors">
                <div className={`hidden sm:flex h-12 w-12 rounded-xl ${activity.bg} items-center justify-center flex-shrink-0`}>
                  <Briefcase className={`h-6 w-6 ${activity.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-base font-medium text-white truncate">{activity.role}</p>
                  <p className="text-sm text-zinc-400 truncate">{activity.company}</p>
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${activity.bg} ${activity.color}`}>
                    {activity.status}
                  </span>
                  <span className="text-xs text-zinc-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {activity.time}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
```

- [ ] **Step 2: Verify types**

Run: `cd /home/ale/Antigravity/huntjob-web/huntjob-web && npx tsc --noEmit`
Expected: no errors mentioning `dashboard/page.tsx`.

- [ ] **Step 3: Manual verification against the real dev server**

Run: `npm run dev`, log in at `http://localhost:3000/auth/login`, go to `/dashboard`.

1. **New user (zero `resumes`, zero `applications`):** confirm the stats show `0` / `0` (not `142`/`89`/`12`/`92`), the activity feed shows the empty state, not fake companies. Paste a real job URL from one of the allowed domains and click "Generar CV" — confirm the URL card is replaced by the PDF upload step (not an immediate apply).
2. Upload a real PDF CV — confirm it parses into the review form with real extracted data (or the "no pudimos leer" message + empty form if the PDF is a scan/image).
3. Click "Guardar y continuar" — confirm it proceeds automatically through the existing apply flow (status messages, result card, docx download) and that a new row appears in `resumes` (check via `node scripts/check-db.mjs` or the Supabase dashboard).
4. Reload `/dashboard` — confirm the activity feed now shows the real application just created, and the stats incremented.
5. Apply to a second URL — confirm it does **not** re-show the PDF capture step (since a `resumes` row now exists), and applies directly.

- [ ] **Step 4: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web
git add huntjob-web/src/app/dashboard/page.tsx
git commit -m "feat: wire dashboard to real Supabase data

Kills the hardcoded activity feed, fake stats (142/89/12/92), and
mockProfile sent to /api/apply. First-time users without a resumes
row now go through CvCaptureForm before their first apply."
```

---

### Task 6: Remove the mock fallback in `applications/page.tsx`

**Files:**
- Modify: `src/app/dashboard/applications/page.tsx:18-85`

**Interfaces:**
- No new interfaces — internal cleanup of an existing page.

- [ ] **Step 1: Remove `mockApplications` and the fallback logic**

In `src/app/dashboard/applications/page.tsx`, replace lines 18-85 (from `const mockApplications: Application[] = [` through the closing `};` of `fetchApplications`) with:

```tsx
export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [newApp, setNewApp] = useState({ company_name: '', job_title: '', status: 'pending' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const supabase = createClient();

  const fetchApplications = async () => {
    setLoading(true);
    setLoadError(false);
    const { data, error } = await supabase
      .from('applications')
      .select('*')
      .order('applied_at', { ascending: false });

    if (error) {
      console.error(error);
      setLoadError(true);
      setApplications([]);
    } else {
      setApplications((data ?? []) as Application[]);
    }
    setLoading(false);
  };
```

- [ ] **Step 2: Add an error banner**

Find (around what is now line ~145 after Step 1's removal):

```tsx
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      {/* Header */}
```

Replace with:

```tsx
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      {loadError && (
        <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-4 flex items-center justify-between">
          <p className="text-sm text-rose-400">No pudimos cargar tus postulaciones.</p>
          <Button variant="outline" size="sm" onClick={fetchApplications} className="border-rose-500/30 text-rose-400 hover:bg-rose-500/10">
            Reintentar
          </Button>
        </div>
      )}
      {/* Header */}
```

- [ ] **Step 3: Make the existing empty state accurate for a truly-empty account**

Find:

```tsx
        {!loading && filteredApps.length === 0 && (
          <div className="col-span-full py-12 text-center border border-dashed border-white/10 rounded-xl bg-zinc-900/20">
            <Building className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
            <p className="text-zinc-400 text-sm">No se encontraron postulaciones</p>
          </div>
        )}
```

Replace with:

```tsx
        {!loading && !loadError && filteredApps.length === 0 && (
          <div className="col-span-full py-12 text-center border border-dashed border-white/10 rounded-xl bg-zinc-900/20">
            <Building className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
            <p className="text-zinc-400 text-sm">
              {applications.length === 0 ? 'Aún no registras postulaciones' : 'No se encontraron postulaciones con ese filtro'}
            </p>
          </div>
        )}
```

- [ ] **Step 4: Verify types**

Run: `cd /home/ale/Antigravity/huntjob-web/huntjob-web && npx tsc --noEmit`
Expected: no errors mentioning `applications/page.tsx`, and no error about an unused `mockApplications`.

- [ ] **Step 5: Manual verification**

Run: `npm run dev`, log in, go to `/dashboard/applications`.

1. On an account with zero real applications: confirm it shows "Aún no registras postulaciones" — never TechNova/Acme Corp/Global Solutions/StartupX.
2. Temporarily rename `NEXT_PUBLIC_SUPABASE_URL` in `.env.local` to something invalid, restart `npm run dev`, reload the page: confirm the red error banner with "Reintentar" appears instead of any application list. Restore `.env.local` afterward.
3. Create a real application via the "Nueva Postulación" form (already-working code path, unchanged): confirm it appears in the grid and the empty state disappears.

- [ ] **Step 6: Commit**

```bash
cd /home/ale/Antigravity/huntjob-web
git add huntjob-web/src/app/dashboard/applications/page.tsx
git commit -m "fix: remove silent mockApplications fallback

A failed or empty query now shows a real error banner or a real
empty state instead of four fake companies."
```

---

## Self-Review Notes

- **Spec coverage:** Section A (architecture) → Tasks 1, 3, 5. Section B (capture flow) → Tasks 1, 3, 4. Section C (dashboard feed + apply) → Task 5. Section D (applications mock fallback) → Task 6. Section E (edge cases) → covered inline in Task 3 (PDF validation, injection check) and Task 4 (never-block-on-parse-failure). Stats Grid addendum → Task 5. The one spec item intentionally *not* built is the `ai_credits_limit` gate — explicitly out of scope per spec.
- **Type consistency checked:** `CVData` (from `docx-generator.ts`) is used identically across Tasks 3, 4, 5 — same field names (`personalInfo`, `summary`, `experience`, `education`, `skills`). `CvCaptureForm`'s `onComplete: (cvData: CVData) => void` matches exactly how Task 5 calls it (`handleCaptureComplete = async (cvData: CVData) => ...`). `ApplicationStatus` in Task 5 matches the four real enum values used in `applications/page.tsx` (`pending`, `interview_scheduled`, `rejected`, `offer`).
- **No placeholders:** every step above has complete, real code — no TBD/TODO, no "add error handling" without showing the handling.
