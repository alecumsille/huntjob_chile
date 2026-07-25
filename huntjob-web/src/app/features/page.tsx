/* eslint-disable @typescript-eslint/no-explicit-any */

"use client";

import { motion } from "framer-motion";
import { Target, Briefcase, Zap, Cpu, Sparkles, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function FeaturesPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
  };

  return (
    <div className="flex-1 flex flex-col pt-12 pb-32 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-indigo-500/10 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-purple-500/10 blur-[150px] rounded-full pointer-events-none" />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10"
      >
        {/* Header */}
        <div className="max-w-4xl mx-auto text-center space-y-8 mb-24">
          <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm text-zinc-300 font-medium backdrop-blur-md">
            <Sparkles className="h-4 w-4 text-indigo-400" />
            <span>Características Premium</span>
          </motion.div>
          <motion.h1 variants={itemVariants} className="text-5xl sm:text-7xl font-heading font-bold text-white tracking-tight">
            Una ventaja injusta en tu <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">búsqueda laboral</span>
          </motion.h1>
          <motion.p variants={itemVariants} className="text-xl text-zinc-400 font-light max-w-2xl mx-auto">
            HuntJob Pro combina Inteligencia Artificial avanzada con automatización inteligente para multiplicar tus posibilidades de contratación.
          </motion.p>
        </div>

        {/* Feature 1: Market Intelligence */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-32">
          <div className="order-2 lg:order-1 relative group">
            <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/20 to-purple-500/20 blur-3xl rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            <div className="relative bg-zinc-900/50 border border-white/10 rounded-3xl p-8 backdrop-blur-sm overflow-hidden">
              <div className="flex flex-col space-y-6">
                {[1, 2, 3].map((_, i) => (
                  <div key={i} className="w-full h-16 bg-white/5 rounded-xl border border-white/5 flex items-center px-4 animate-pulse" style={{ animationDelay: `${i * 200}ms` }}>
                    <div className="h-4 w-4 rounded-full bg-indigo-400/50 mr-4" />
                    <div className="flex-1 space-y-2">
                      <div className="h-2 bg-white/10 rounded w-1/3" />
                      <div className="h-2 bg-white/10 rounded w-1/2" />
                    </div>
                    <div className="h-6 w-16 bg-emerald-400/10 rounded-full border border-emerald-400/20 flex items-center justify-center">
                      <span className="text-[10px] text-emerald-400 font-bold">98% Match</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="order-1 lg:order-2 space-y-6">
            <div className="h-12 w-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-6">
              <Target className="h-6 w-6 text-indigo-400" />
            </div>
            <h2 className="text-3xl sm:text-4xl font-heading font-bold text-white">Inteligencia de Mercado en Tiempo Real</h2>
            <p className="text-lg text-zinc-400 font-light leading-relaxed">
              Nuestros algoritmos escanean constantemente las bolsas de trabajo globales para identificar las palabras clave, habilidades blandas y tecnologías exactas que los reclutadores están exigiendo hoy mismo.
            </p>
            <ul className="space-y-3 pt-4">
              <li className="flex items-center text-zinc-300"><CheckCircle2 className="h-5 w-5 text-emerald-400 mr-3" /> Extracción de Keywords Críticas</li>
              <li className="flex items-center text-zinc-300"><CheckCircle2 className="h-5 w-5 text-emerald-400 mr-3" /> Análisis de Salarios por Región</li>
              <li className="flex items-center text-zinc-300"><CheckCircle2 className="h-5 w-5 text-emerald-400 mr-3" /> Tendencias de Contratación</li>
            </ul>
          </div>
        </motion.div>

        {/* Feature 2: Profile Optimization */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-32">
          <div className="space-y-6">
            <div className="h-12 w-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-6">
              <Cpu className="h-6 w-6 text-purple-400" />
            </div>
            <h2 className="text-3xl sm:text-4xl font-heading font-bold text-white">Refinamiento y Score ATS</h2>
            <p className="text-lg text-zinc-400 font-light leading-relaxed">
              El 75% de los currículums nunca son leídos por un humano. HuntJob audita tu perfil contra los sistemas ATS (Applicant Tracking Systems) y reescribe tu experiencia laboral para garantizar que pases el filtro.
            </p>
            <ul className="space-y-3 pt-4">
              <li className="flex items-center text-zinc-300"><CheckCircle2 className="h-5 w-5 text-emerald-400 mr-3" /> Generación de Impacto Cuantificable</li>
              <li className="flex items-center text-zinc-300"><CheckCircle2 className="h-5 w-5 text-emerald-400 mr-3" /> Ajuste de Formato ATS-Friendly</li>
              <li className="flex items-center text-zinc-300"><CheckCircle2 className="h-5 w-5 text-emerald-400 mr-3" /> Optimización de Perfil de LinkedIn</li>
            </ul>
          </div>
          <div className="relative group">
            <div className="absolute inset-0 bg-gradient-to-bl from-purple-500/20 to-pink-500/20 blur-3xl rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            <div className="relative bg-zinc-900/50 border border-white/10 rounded-3xl p-8 backdrop-blur-sm overflow-hidden h-80 flex flex-col items-center justify-center">
              <div className="relative w-48 h-48">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" className="text-white/5" strokeWidth="8" />
                  <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" className="text-purple-500" strokeWidth="8" strokeDasharray="283" strokeDashoffset="42" strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-4xl font-heading font-bold text-white">85<span className="text-2xl text-zinc-500">/100</span></span>
                  <span className="text-xs text-zinc-400 mt-1 uppercase tracking-wider">Score ATS</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Feature 3: Auto Pilot */}
        <motion.div variants={itemVariants as any} className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-32">
          <div className="order-2 lg:order-1 relative group">
            <div className="absolute inset-0 bg-gradient-to-tr from-pink-500/20 to-rose-500/20 blur-3xl rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            <div className="relative bg-zinc-900/50 border border-white/10 rounded-3xl p-8 backdrop-blur-sm overflow-hidden flex items-center justify-center">
              <div className="w-full space-y-4">
                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10">
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 bg-indigo-500/20 rounded-lg flex items-center justify-center">
                      <Briefcase className="h-5 w-5 text-indigo-400" />
                    </div>
                    <div>
                      <div className="text-white font-medium">Senior Frontend Engineer</div>
                      <div className="text-zinc-500 text-sm">TechCorp Inc.</div>
                    </div>
                  </div>
                  <div className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 text-xs font-bold">Enviado</div>
                </div>
                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10 opacity-70">
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                      <Briefcase className="h-5 w-5 text-blue-400" />
                    </div>
                    <div>
                      <div className="text-white font-medium">Product Manager</div>
                      <div className="text-zinc-500 text-sm">Fintech Solutions</div>
                    </div>
                  </div>
                  <div className="px-3 py-1 bg-amber-500/10 border border-amber-500/20 rounded-full text-amber-400 text-xs font-bold">Generando CV</div>
                </div>
              </div>
            </div>
          </div>
          <div className="order-1 lg:order-2 space-y-6">
            <div className="h-12 w-12 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center mb-6">
              <Zap className="h-6 w-6 text-pink-400" />
            </div>
            <h2 className="text-3xl sm:text-4xl font-heading font-bold text-white">Postulación en Piloto Automático</h2>
            <p className="text-lg text-zinc-400 font-light leading-relaxed">
              Define tus preferencias laborales y deja que nuestros agentes busquen, generen cartas de presentación únicas para cada oferta, y envíen las postulaciones por ti 24/7.
            </p>
            <ul className="space-y-3 pt-4">
              <li className="flex items-center text-zinc-300"><CheckCircle2 className="h-5 w-5 text-emerald-400 mr-3" /> Generación de Cover Letters con IA</li>
              <li className="flex items-center text-zinc-300"><CheckCircle2 className="h-5 w-5 text-emerald-400 mr-3" /> Envío Automático de CV Adaptado</li>
              <li className="flex items-center text-zinc-300"><CheckCircle2 className="h-5 w-5 text-emerald-400 mr-3" /> Dashboard de Seguimiento Centralizado</li>
            </ul>
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div variants={itemVariants as any} className="text-center mt-20 p-12 bg-white/5 border border-white/10 rounded-3xl backdrop-blur-xl relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/10 to-transparent pointer-events-none" />
          <h2 className="text-3xl sm:text-5xl font-heading font-bold text-white mb-6 relative z-10">¿Listo para conseguir tu trabajo ideal?</h2>
          <p className="text-zinc-400 mb-10 max-w-xl mx-auto relative z-10">
            Únete a cientos de profesionales que están acelerando sus carreras profesionales con IA.
          </p>
          {/* @ts-expect-error shadcn ui base-ui button doesn't expose asChild natively */}
          <Button asChild size="lg" className="h-14 px-8 rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white border-0 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 font-bold text-lg relative z-10 shadow-[0_0_30px_rgba(139,92,246,0.3)] hover:shadow-[0_0_50px_rgba(139,92,246,0.5)] transition-all duration-300">
            <Link href="/auth/login">
              Comenzar Gratis ahora
            </Link>
          </Button>
        </motion.div>
      </motion.div>
    </div>
  );
}
