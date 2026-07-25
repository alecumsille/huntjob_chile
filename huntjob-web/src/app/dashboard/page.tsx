"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  TrendingUp, 
  Send, 
  Eye, 
  CheckCircle2, 
  Clock,
  ArrowUpRight,
  MoreHorizontal,
  Briefcase,
  Link as LinkIcon,
  Loader2,
  FileText,
  Download
} from "lucide-react";

export default function DashboardPage() {
  const [url, setUrl] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [workflowStatus, setWorkflowStatus] = useState("");
  const [result, setResult] = useState<any>(null);

  const [activities, setActivities] = useState([
    { role: "Senior Frontend Engineer", company: "Stripe", status: "Enviado por IA", time: "Hace 2 horas", color: "text-emerald-400", bg: "bg-emerald-500/10" },
    { role: "React Developer", company: "Vercel", status: "Curriculum Optimizado", time: "Hace 5 horas", color: "text-indigo-400", bg: "bg-indigo-500/10" },
    { role: "Fullstack Developer", company: "Airbnb", status: "Match 98% Encontrado", time: "Ayer", color: "text-purple-400", bg: "bg-purple-500/10" },
    { role: "Software Engineer", company: "Meta", status: "Entrevista Agendada", time: "Ayer", color: "text-pink-400", bg: "bg-pink-500/10" },
  ]);
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  const handleApply = async () => {
    if (!url) return;
    setIsProcessing(true);
    setResult(null);
    setWorkflowStatus("1/3: Iniciando scraper para leer la oferta...");

    try {
      // Perfil de prueba para el flujo (mock)
      const mockProfile = {
        personalInfo: {
          name: "Alejandro Developer",
          email: "ale@example.com",
          phone: "+1 234 567 8900",
          linkedin: "linkedin.com/in/aledev",
          location: "Remoto, LATAM"
        },
        summary: "Ingeniero de Software con experiencia diseñando e implementando soluciones usando React y Node.js.",
        experience: [
          {
            company: "TechNova",
            position: "Frontend Engineer",
            startDate: "Ene 2021",
            endDate: "Presente",
            achievements: ["Lideré migraciones a Next.js", "Mejoré web vitals"]
          }
        ],
        education: [{ institution: "Universidad", degree: "Ingeniería", graduationDate: "2017" }],
        skills: ["React", "TypeScript", "Node.js"]
      };

      // Fase 1: Enviar al orquestador
      setWorkflowStatus("2/3: Oferta leída. IA adaptando el CV...");
      const res = await fetch('/api/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, profile: mockProfile })
      });

      if (!res.ok) throw new Error("Error en la orquestación");

      const data = await res.json();
      setWorkflowStatus("3/3: ¡CV Optimizado con éxito!");
      setResult(data);

      setActivities(prev => [
        { 
          role: data.jobOffer.title || "Nuevo Rol", 
          company: data.jobOffer.company || "Nueva Empresa", 
          status: "Curriculum Optimizado", 
          time: "Justo ahora", 
          color: "text-indigo-400", 
          bg: "bg-indigo-500/10" 
        },
        ...prev
      ]);
    } catch (e) {
      console.error(e);
      setWorkflowStatus("Error al procesar la oferta.");
    } finally {
      setIsProcessing(false);
    }
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
      a.download = `CV_Optimizado_${result.jobOffer.company.replace(/ /g, '_')}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(objUrl);
    } catch(e) {
      alert("Error descargando el DOCX");
    }
  };

  const stats = [
    {
      title: "Postulaciones Automáticas",
      value: "142",
      change: "+12%",
      trend: "up",
      icon: Send,
      color: "text-indigo-400",
      bg: "bg-indigo-500/10",
      border: "border-indigo-500/20"
    },
    {
      title: "Vistas de Reclutadores",
      value: "89",
      change: "+24%",
      trend: "up",
      icon: Eye,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20"
    },
    {
      title: "Entrevistas Agendadas",
      value: "12",
      change: "+4",
      trend: "up",
      icon: CheckCircle2,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      border: "border-purple-500/20"
    },
    {
      title: "Score ATS Promedio",
      value: "92/100",
      change: "+5 pts",
      trend: "up",
      icon: TrendingUp,
      color: "text-pink-400",
      bg: "bg-pink-500/10",
      border: "border-pink-500/20"
    }
  ];

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <motion.div variants={itemVariants}>
          <h1 className="text-3xl font-heading font-bold text-white mb-2">Tu Panel de Impacto</h1>
          <p className="text-zinc-400">Automatiza tu búsqueda de empleo con el motor de Inteligencia Artificial.</p>
        </motion.div>
      </div>

      {/* The Master Loop - Magic Input */}
      <motion.div variants={itemVariants} className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-2xl p-6 relative overflow-hidden">
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
                      Adaptado para el rol de <strong className="text-white">{result.jobOffer.title}</strong> en <strong className="text-white">{result.jobOffer.company}</strong>
                    </p>
                    <div className="flex flex-wrap gap-2 mt-3">
                      {result.jobOffer.keywords?.slice(0, 5).map((kw: string, idx: number) => (
                        <span key={idx} className="text-xs bg-white/10 text-zinc-300 px-2 py-1 rounded-md">
                          {kw}
                        </span>
                      ))}
                    </div>
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
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
              <span className="flex items-center text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-full">
                {stat.change}
                <ArrowUpRight className="h-3 w-3 ml-1" />
              </span>
            </div>
            
            <div className="relative z-10">
              <h3 className="text-3xl font-heading font-bold text-white mb-1">{stat.value}</h3>
              <p className="text-sm text-zinc-400 font-medium">{stat.title}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Recent Activity */}
      <motion.div variants={itemVariants} className="bg-zinc-900/50 border border-white/10 rounded-2xl backdrop-blur-sm overflow-hidden">
        <div className="p-6 border-b border-white/10 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">Actividad Reciente</h2>
          <button className="text-sm text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
            Ver todo
          </button>
        </div>
        
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
              <button className="hidden sm:block p-2 text-zinc-500 hover:text-white transition-colors ml-2">
                <MoreHorizontal className="h-5 w-5" />
              </button>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
