"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, FileText, MoreVertical, Edit2, Eye, Download, Loader2 } from "lucide-react";

export default function ResumesPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  const resumes = [
    { id: 1, name: "CV Frontend Principal", role: "Senior Frontend Engineer", score: 95, updatedAt: "Hace 2 horas" },
    { id: 2, name: "CV Fullstack General", role: "Fullstack Developer", score: 88, updatedAt: "Hace 3 días" },
    { id: 3, name: "CV Tech Lead (Mgmt)", role: "Engineering Manager", score: 92, updatedAt: "La semana pasada" },
  ];

  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  const handleDownloadWord = async (id: number) => {
    setDownloadingId(id);
    try {
      // Mock data for MVP test
      const payload = {
        personalInfo: {
          name: "Alejandro Developer",
          email: "ale@example.com",
          phone: "+1 234 567 8900",
          linkedin: "linkedin.com/in/aledev",
          location: "Remoto, LATAM"
        },
        summary: "Ingeniero de Software con más de 5 años de experiencia diseñando e implementando soluciones escalables usando React, Node.js y arquitecturas cloud. Apasionado por la optimización de rendimiento y la experiencia de usuario.",
        experience: [
          {
            company: "TechNova Inc.",
            position: "Senior Frontend Engineer",
            startDate: "Ene 2021",
            endDate: "Presente",
            achievements: [
              "Lideré la migración del monolito a micro-frontends (Next.js), reduciendo el tiempo de carga en un 45%.",
              "Implementé sistema de diseño (Design System) propio utilizando TailwindCSS y Radix UI, ahorrando un 30% del tiempo de desarrollo a 4 equipos.",
              "Mejoré el Core Web Vitals (LCP) de 4.2s a 1.8s mediante Server-Side Rendering y optimización de imágenes."
            ]
          },
          {
            company: "Acme Corp",
            position: "Full Stack Developer",
            startDate: "Mar 2018",
            endDate: "Dic 2020",
            achievements: [
              "Desarrollé la API principal en Node.js/Express, manejando más de 1M de peticiones diarias con 99.9% de uptime.",
              "Automaticé procesos de testing e integración continua (CI/CD) con GitHub Actions, reduciendo los bugs en producción en un 20%."
            ]
          }
        ],
        education: [
          {
            institution: "Universidad Tecnológica",
            degree: "Ingeniería de Software",
            graduationDate: "Dic 2017"
          }
        ],
        skills: ["React", "Next.js", "TypeScript", "Node.js", "TailwindCSS", "PostgreSQL", "AWS", "Git"]
      };

      const res = await fetch('/api/export/docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error("Error en la descarga");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `CV_Optimizado_${id}.docx`;
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

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <motion.div variants={itemVariants}>
          <h1 className="text-3xl font-heading font-bold text-white mb-2">Mis Currículums</h1>
          <p className="text-zinc-400">Administra tus CVs optimizados por IA.</p>
        </motion.div>
        <motion.div variants={itemVariants}>
          <button className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white font-bold rounded-lg transition-colors flex items-center gap-2 text-sm">
            <Plus className="h-4 w-4" />
            Crear Nuevo CV
          </button>
        </motion.div>
      </div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {resumes.map((resume) => (
          <div key={resume.id} className="bg-zinc-900/50 border border-white/10 rounded-2xl p-6 relative overflow-hidden group hover:border-indigo-500/50 transition-colors">
            <div className="flex justify-between items-start mb-6">
              <div className="h-12 w-12 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                <FileText className="h-6 w-6 text-indigo-400" />
              </div>
              <button className="text-zinc-500 hover:text-white transition-colors">
                <MoreVertical className="h-5 w-5" />
              </button>
            </div>
            
            <h3 className="text-lg font-bold text-white mb-1 truncate">{resume.name}</h3>
            <p className="text-sm text-zinc-400 mb-6">{resume.role}</p>

            <div className="flex items-center justify-between mt-auto">
              <div className="flex flex-col">
                <span className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Score ATS</span>
                <span className={`text-sm font-bold ${resume.score >= 90 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {resume.score}/100
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => handleDownloadWord(resume.id)}
                  disabled={downloadingId === resume.id}
                  title="Descargar en Word (.docx)"
                  className="p-2 bg-indigo-500/10 hover:bg-indigo-500/20 rounded-lg text-indigo-400 transition-colors disabled:opacity-50"
                >
                  {downloadingId === resume.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                </button>
                <button className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-zinc-300 transition-colors">
                  <Eye className="h-4 w-4" />
                </button>
                <button className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-zinc-300 transition-colors">
                  <Edit2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}
