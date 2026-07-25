"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Plus, FileText, Download, Loader2, Sparkles } from "lucide-react";
import { createClient } from "@/utils/supabase/client";
import Link from "next/link";

interface Resume {
  id: string;
  name: string;
  target_company?: string;
  target_role?: string;
  cv_data: any;
  created_at: string;
}

export default function ResumesPage() {
  const supabase = createClient();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    async function loadResumes() {
      try {
        const { data, error } = await supabase
          .from("resumes")
          .select("*")
          .order("created_at", { ascending: false });

        if (data && !error) {
          setResumes(data as Resume[]);
        }
      } catch (err) {
        console.error("Error fetching resumes:", err);
      } finally {
        setLoading(false);
      }
    }
    loadResumes();
  }, []);

  const handleDownloadWord = async (resume: Resume) => {
    setDownloadingId(resume.id);
    try {
      const res = await fetch('/api/export/docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(resume.cv_data)
      });

      if (!res.ok) throw new Error("Error en la descarga");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${resume.name.replace(/\s+/g, '_')}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      alert("Hubo un error al descargar el CV.");
    } finally {
      setDownloadingId(null);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <motion.div variants={itemVariants}>
          <h1 className="text-3xl font-heading font-bold text-white mb-2">Mis Currículums</h1>
          <p className="text-zinc-400">Administra y descarga tus CVs optimizados por Inteligencia Artificial.</p>
        </motion.div>
        <motion.div variants={itemVariants}>
          <Link 
            href="/dashboard" 
            className="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-bold rounded-xl transition-all shadow-lg shadow-indigo-500/20 flex items-center gap-2 text-sm"
          >
            <Sparkles className="h-4 w-4" />
            Optimizar Nuevo CV
          </Link>
        </motion.div>
      </div>

      {loading ? (
        <div className="py-20 flex justify-center items-center">
          <Loader2 className="h-8 w-8 text-indigo-400 animate-spin" />
        </div>
      ) : resumes.length === 0 ? (
        <div className="p-12 text-center bg-zinc-900/30 border border-white/5 rounded-3xl backdrop-blur-md">
          <FileText className="h-16 w-16 text-indigo-400/40 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">Aún no tienes currículums adaptados</h3>
          <p className="text-zinc-400 max-w-md mx-auto mb-6">
            Pega el link de cualquier oferta laboral en el Dashboard y la IA generará un CV optimizado ATS para ti.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-indigo-600 text-white font-bold hover:bg-indigo-500 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Ir al Dashboard
          </Link>
        </div>
      ) : (
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {resumes.map((resume) => (
            <div key={resume.id} className="bg-zinc-900/50 border border-white/10 rounded-2xl p-6 relative overflow-hidden group hover:border-indigo-500/50 transition-colors flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-4">
                  <div className="h-12 w-12 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                    <FileText className="h-6 w-6 text-indigo-400" />
                  </div>
                  <span className="text-xs text-zinc-500">
                    {new Date(resume.created_at).toLocaleDateString("es-CL")}
                  </span>
                </div>
                
                <h3 className="text-lg font-bold text-white mb-1 truncate" title={resume.name}>{resume.name}</h3>
                <p className="text-sm text-zinc-400 mb-4">{resume.target_role || "CV Optimizado ATS"}</p>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-white/5 mt-4">
                <span className="text-xs font-bold text-emerald-400 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                  ATS Match Ready
                </span>
                
                <button 
                  onClick={() => handleDownloadWord(resume)}
                  disabled={downloadingId === resume.id}
                  title="Descargar en Word (.docx)"
                  className="px-4 py-2 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 rounded-lg font-medium text-xs transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  {downloadingId === resume.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Download className="h-4 w-4" />
                      Descargar .docx
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}
