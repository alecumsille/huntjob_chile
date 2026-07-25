"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Sparkles, Briefcase, Zap, Target, LineChart, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center pt-24 pb-32 px-4 sm:px-6 lg:px-8 text-center relative overflow-hidden min-h-screen">
      {/* Decorative premium background elements */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-purple-500/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 translate-x-1/4 translate-y-1/4 w-[600px] h-[500px] bg-indigo-500/10 blur-[150px] rounded-full pointer-events-none" />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="max-w-5xl mx-auto space-y-12 relative z-10"
      >
        <motion.div variants={itemVariants} className="flex justify-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm text-zinc-300 font-medium shadow-[0_0_20px_rgba(255,255,255,0.05)] backdrop-blur-md">
            <Sparkles className="h-4 w-4 text-purple-400" />
            <span>HuntJob Chile - Plataforma Inteligente de Empleos</span>
          </div>
        </motion.div>

        <motion.h1 
          variants={itemVariants}
          className="text-6xl sm:text-8xl font-heading font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-white via-zinc-200 to-zinc-500 pb-2"
        >
          HuntJob <br className="hidden sm:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-indigo-400 to-purple-400 animate-gradient-x">
            Chile
          </span>
        </motion.h1>

        <motion.p 
          variants={itemVariants}
          className="text-xl sm:text-2xl text-zinc-400 max-w-3xl mx-auto font-light leading-relaxed"
        >
          La suite de aceleración laboral diseñada para profesionales y talentos en Chile. Busca en tiempo real en los principales portales del país, audita tu perfil con IA y genera currículums listos para superar los filtros ATS.
        </motion.p>

        <motion.div 
          variants={itemVariants}
          className="flex flex-col sm:flex-row items-center justify-center gap-6 pt-8"
        >
          <Button 
            // @ts-expect-error shadcn ui base-ui button doesn't expose asChild natively
            asChild
            size="lg" 
            className="h-16 px-10 rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 font-bold text-lg w-full sm:w-auto shadow-[0_0_40px_rgba(139,92,246,0.3)] hover:shadow-[0_0_60px_rgba(139,92,246,0.5)] border-0 transition-all duration-300 transform hover:-translate-y-1 group"
          >
            <Link href="/dashboard">
              Comenzar Optimización
            </Link>
          </Button>
          
          <Button 
            // @ts-expect-error shadcn ui base-ui button doesn't expose asChild natively
            asChild
            size="lg" 
            variant="outline"
            className="h-16 px-10 rounded-full bg-black/20 border-white/10 hover:bg-white/10 hover:border-white/20 hover:text-white text-white font-medium text-lg w-full sm:w-auto backdrop-blur-md transition-all duration-300"
          >
            <Link href="/features">
              <Zap className="mr-3 h-5 w-5 text-zinc-400" />
              Ver Características
            </Link>
          </Button>
        </motion.div>

        {/* Feature Highlights Grid */}
        <motion.div 
          variants={containerVariants}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-24 text-left"
        >
          {[
            {
              title: "Búsqueda Multi-Portal",
              description: "Indexación agregada en tiempo real en los portales más importantes de Chile sin perder tiempo abriendo decenas de pestañas.",
              icon: Target,
              color: "text-indigo-400",
              bg: "bg-indigo-400/10",
              border: "border-indigo-400/20"
            },
            {
              title: "Auditoría ATS en Vivo",
              description: "Recibe un score 0-100%, descubre fortalezas y las palabras clave exactas que le faltan a tu CV para la vacante.",
              icon: LineChart,
              color: "text-purple-400",
              bg: "bg-purple-400/10",
              border: "border-purple-400/20"
            },
            {
              title: "Generador de CVs PDF",
              description: "Produce documentos estructurados y listos para enviar en 4 paletas de diseño ejecutivo diseñadas para superar los filtros ATS.",
              icon: Briefcase,
              color: "text-pink-400",
              bg: "bg-pink-400/10",
              border: "border-pink-400/20"
            }
          ].map((feature, i) => (
            <motion.div 
              key={i}
              variants={itemVariants}
              whileHover={{ y: -5, scale: 1.02 }}
              className="flex flex-col p-8 rounded-3xl bg-zinc-900/40 border border-white/5 backdrop-blur-md transition-all hover:bg-zinc-800/50 hover:border-white/10 group"
            >
              <div className={`p-4 w-16 h-16 rounded-2xl ${feature.bg} ${feature.border} border mb-6 shadow-inner flex items-center justify-center group-hover:scale-110 transition-transform`}>
                <feature.icon className={`h-8 w-8 ${feature.color}`} />
              </div>
              <h3 className="text-xl font-heading font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-base text-zinc-400 leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Value Proposition */}
        <motion.div 
          variants={itemVariants}
          className="pt-20 pb-10"
        >
          <div className="flex flex-wrap justify-center gap-x-8 gap-y-4 text-sm font-medium text-zinc-400">
            <span className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" /> Búsqueda inteligente</span>
            <span className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" /> Matching perfecto</span>
            <span className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" /> Seguimiento en tiempo real</span>
          </div>
        </motion.div>

      </motion.div>
    </div>
  );
}
