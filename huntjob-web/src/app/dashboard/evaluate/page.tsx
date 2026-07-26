"use client";

import { useState } from "react";
import { createClient } from "@/utils/supabase/client";
import { Card } from "@/components/ui/card";
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
  cvMatch: {
    overallScore: number;
    dimensions: { hardSkills: number; seniority: number; education: number; softSkills: number };
    missingKeywords: string[];
    criticalFeedback: string;
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
  // URL efectivamente evaluada (capturada al momento de setear el reporte),
  // para que editar el input despues de evaluar no desincronice el link
  // entre la postulacion y la evaluacion que la origino (ver handleApply).
  const [evaluatedUrl, setEvaluatedUrl] = useState<string | null>(null);
  // CV base ya resuelto en handleEvaluate, reusado en handleApply para no
  // volver a golpear la tabla resumes.
  const [baseProfile, setBaseProfile] = useState<unknown>(null);

  const supabase = createClient();

  const handleUrlChange = (value: string) => {
    setUrl(value);
    // Si ya habia un reporte generado, editar la URL lo invalida: sin esto
    // se podria postular con un evaluationId que apunta a una oferta distinta.
    if (report) {
      setReport(null);
      setEvaluatedUrl(null);
    }
  };

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    setEvaluatedUrl(null);
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
      setBaseProfile(profile);

      const res = await fetch("/api/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, profile }),
      });
      const json: EvaluateResponse = await res.json();
      if (!res.ok) {
        // El catch-all de /api/evaluate (500) devuelve un mensaje generico en
        // ingles; para los demas codigos (400/403/413/422) la ruta ya
        // responde con un mensaje en espanol pensado para mostrarse tal cual.
        setError(
          res.status === 500
            ? "No se pudo evaluar la oferta. Intenta de nuevo en unos minutos."
            : json.error || "No se pudo evaluar la oferta."
        );
      } else {
        setReport(json);
        setEvaluatedUrl(url);
      }
    } catch {
      setError("Error de red evaluando la oferta.");
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!report || !evaluatedUrl) return;
    setApplying(true);
    setError(null);
    try {
      if (!baseProfile) {
        setError("Necesitas subir tu CV base antes de postular.");
        return;
      }

      // El insert de job_evaluations en /api/evaluate puede fallar en silencio
      // (comportamiento heredado de /api/apply) y devolver evaluationId: null.
      // El esquema de /api/apply valida evaluationId como string uuid opcional,
      // así que null explícito rebota con 400 -- solo lo mandamos si es un
      // string real, para que la postulación siga adelante igual (sin el
      // vínculo a la evaluación).
      const body: { url: string; profile: unknown; evaluationId?: string } = {
        url: evaluatedUrl,
        profile: baseProfile,
      };
      if (report.evaluationId) {
        body.evaluationId = report.evaluationId;
      }

      const res = await fetch("/api/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
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
              onChange={(e) => handleUrlChange(e.target.value)}
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
            <Badge variant="outline" className="mb-2">
              Match con tu CV · {(1.0 + (report.cvMatch.overallScore / 100) * 4.0).toFixed(1)}
            </Badge>
            <p className="text-sm text-zinc-300">{report.cvMatch.criticalFeedback}</p>
            {report.cvMatch.missingKeywords.length > 0 && (
              <div className="mt-3">
                <p className="text-xs text-zinc-500 mb-1.5">Palabras clave que le faltan a tu CV:</p>
                <div className="flex flex-wrap gap-1.5">
                  {report.cvMatch.missingKeywords.map((kw, i) => (
                    <Badge key={i} variant="outline" className="text-xs text-amber-400 border-amber-500/30">
                      {kw}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
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
