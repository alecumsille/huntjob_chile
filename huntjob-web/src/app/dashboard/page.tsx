"use client";

import { useCallback, useEffect, useState } from "react";
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
  const [activitiesError, setActivitiesError] = useState(false);
  const [statsData, setStatsData] = useState({ totalApplications: 0, interviewsScheduled: 0 });

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  const loadDashboardData = useCallback(async () => {
    setActivitiesLoading(true);
    setActivitiesError(false);

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

    if (recentRes.error || allRes.error) {
      console.error(recentRes.error || allRes.error);
      setActivitiesError(true);
      setActivitiesLoading(false);
      return;
    }

    setActivities((recentRes.data as ApplicationRow[]).map(toActivity));

    const rows = allRes.data as { status: ApplicationStatus }[];
    setStatsData({
      totalApplications: rows.length,
      interviewsScheduled: rows.filter((r) => r.status === "interview_scheduled").length,
    });

    setActivitiesLoading(false);
  }, [supabase]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

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

      // Re-fetch real state instead of splicing an optimistic entry — avoids racing
      // with the initial-load effect and keeps a single source of truth.
      await loadDashboardData();
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

    const { data: resumes, error: resumesError } = await supabase
      .from("resumes")
      .select("cv_data")
      .eq("user_id", user.id)
      .is("target_company", null)
      .order("created_at", { ascending: false })
      .limit(1);

    if (resumesError) {
      console.error(resumesError);
      setIsProcessing(false);
      setWorkflowStatus("No pudimos verificar tu CV guardado. Intenta de nuevo.");
      return;
    }

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

    const { error: insertError } = await supabase.from("resumes").insert({
      user_id: user.id,
      name: "Mi CV Base",
      cv_data: cvData,
    });

    if (insertError) {
      console.error(insertError);
      setWorkflowStatus("No pudimos guardar tu CV. Intenta de nuevo.");
      return;
    }

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

        {activitiesError ? (
          <div className="p-6">
            <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <p className="text-sm text-rose-300">No pudimos cargar tu actividad reciente.</p>
              <button
                onClick={() => loadDashboardData()}
                className="px-3 py-1.5 text-sm font-medium bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 rounded-lg transition-colors flex-shrink-0"
              >
                Reintentar
              </button>
            </div>
          </div>
        ) : activitiesLoading ? (
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
