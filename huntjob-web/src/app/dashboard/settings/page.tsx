"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  User, 
  Briefcase, 
  Bell, 
  CreditCard,
  UploadCloud,
  DollarSign,
  Laptop,
  CheckCircle,
  Loader2,
  Zap,
  ExternalLink,
  ShieldCheck
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle,
  CardFooter
} from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { createClient } from "@/utils/supabase/client";

export default function SettingsPage() {
  const supabase = createClient();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const [profile, setProfile] = useState({
    full_name: "",
    phone: "",
    linkedin_url: "",
    location: "",
    desired_role: "",
    salary_expectation: "",
    work_modality: "",
    professional_summary: "",
    plan: "free",
    ai_credits_used: 0,
    ai_credits_limit: 10,
  });

  useEffect(() => {
    async function loadProfile() {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        const { data, error } = await supabase
          .from("profiles")
          .select("*")
          .eq("id", user.id)
          .single();

        if (data && !error) {
          setProfile({
            full_name: data.full_name || "",
            phone: data.phone || "",
            linkedin_url: data.linkedin_url || "",
            location: data.location || "",
            desired_role: data.desired_role || "",
            salary_expectation: data.salary_expectation || "",
            work_modality: data.work_modality || "",
            professional_summary: data.professional_summary || "",
            plan: data.plan || "free",
            ai_credits_used: data.ai_credits_used || 0,
            ai_credits_limit: data.ai_credits_limit || 10,
          });
        }
      } catch (err) {
        console.error("Error loading profile:", err);
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaveSuccess(false);
    setErrorMsg("");

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        setErrorMsg("Debes iniciar sesión.");
        setSaving(false);
        return;
      }

      const { error } = await supabase
        .from("profiles")
        .upsert({
          id: user.id,
          email: user.email,
          full_name: profile.full_name,
          phone: profile.phone,
          linkedin_url: profile.linkedin_url,
          location: profile.location,
          desired_role: profile.desired_role,
          salary_expectation: profile.salary_expectation,
          work_modality: profile.work_modality,
          professional_summary: profile.professional_summary,
          updated_at: new Date().toISOString(),
        });

      if (error) {
        throw error;
      }

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: unknown) {
      console.error("Error saving profile:", err);
      setErrorMsg(err instanceof Error ? err.message : "Error al guardar el perfil");
    } finally {
      setSaving(false);
    }
  };

  const handleUpgradeFlow = async (planKey: string) => {
    setPaymentLoading(true);
    setErrorMsg("");
    try {
      const res = await fetch("/api/payments/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan: planKey }),
      });

      const data = await res.json();
      if (!res.ok || !data.url) {
        throw new Error(data.error || "No se pudo generar la orden de pago");
      }

      // Redirigir a Flow.cl
      window.location.href = data.url;
    } catch (err: unknown) {
      console.error("Error iniciando pago Flow:", err);
      setErrorMsg(err instanceof Error ? err.message : "Error al conectar con Flow.cl");
      setPaymentLoading(false);
    }
  };

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

  return (
    <div className="flex-1 flex flex-col pt-24 pb-32 relative overflow-hidden min-h-screen">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-purple-500/10 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-indigo-500/10 blur-[150px] rounded-full pointer-events-none" />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-5xl relative z-10"
      >
        <motion.div variants={itemVariants} className="mb-10">
          <h1 className="text-4xl font-heading font-bold text-white mb-2">Configuración</h1>
          <p className="text-zinc-400">Gestiona tus preferencias, perfil profesional y ajustes de suscripción.</p>
        </motion.div>

        {saveSuccess && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center gap-3">
            <CheckCircle className="h-5 w-5 shrink-0" />
            <span>¡Tus preferencias han sido guardadas correctamente!</span>
          </div>
        )}

        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center gap-3">
            <ShieldCheck className="h-5 w-5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <motion.div variants={itemVariants}>
          <Tabs defaultValue="profile" className="w-full flex flex-col md:flex-row gap-8">
            <TabsList className="flex md:flex-col h-auto w-full md:w-64 bg-zinc-900/50 border border-white/5 p-2 rounded-2xl backdrop-blur-md justify-start overflow-x-auto gap-2">
              <TabsTrigger 
                value="profile" 
                className="w-full justify-start gap-3 px-4 py-3 rounded-xl text-left data-[state=active]:bg-white/10 data-[state=active]:text-white text-zinc-400"
              >
                <Briefcase className="h-5 w-5" />
                Perfil y Preferencias
              </TabsTrigger>
              <TabsTrigger 
                value="account" 
                className="w-full justify-start gap-3 px-4 py-3 rounded-xl text-left data-[state=active]:bg-white/10 data-[state=active]:text-white text-zinc-400"
              >
                <User className="h-5 w-5" />
                Cuenta
              </TabsTrigger>
              <TabsTrigger 
                value="notifications" 
                className="w-full justify-start gap-3 px-4 py-3 rounded-xl text-left data-[state=active]:bg-white/10 data-[state=active]:text-white text-zinc-400"
              >
                <Bell className="h-5 w-5" />
                Notificaciones
              </TabsTrigger>
              <TabsTrigger 
                value="billing" 
                className="w-full justify-start gap-3 px-4 py-3 rounded-xl text-left data-[state=active]:bg-white/10 data-[state=active]:text-white text-zinc-400"
              >
                <CreditCard className="h-5 w-5" />
                Suscripción Flow
              </TabsTrigger>
            </TabsList>

            <div className="flex-1">
              <TabsContent value="profile" className="mt-0 space-y-6">
                
                <Card className="bg-zinc-900/50 border-white/5 backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-xl text-white">Datos Personales</CardTitle>
                    <CardDescription className="text-zinc-400">
                      Información de contacto que se usará para tus postulaciónes.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-zinc-300">Nombre Completo</Label>
                        <Input 
                          value={profile.full_name}
                          onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                          placeholder="Ej: Alejandro Cumsille"
                          className="bg-black/20 border-white/10 text-white placeholder:text-zinc-600 focus-visible:ring-indigo-500"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-zinc-300">Teléfono / WhatsApp</Label>
                        <Input 
                          value={profile.phone}
                          onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                          placeholder="+56 9 1234 5678"
                          className="bg-black/20 border-white/10 text-white placeholder:text-zinc-600 focus-visible:ring-indigo-500"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-900/50 border-white/5 backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-xl text-white">Preferencias Laborales</CardTitle>
                    <CardDescription className="text-zinc-400">
                      Define qué estás buscando para que la IA adapte tus postulaciones.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="role" className="text-zinc-300">Rol o Cargo Deseado</Label>
                      <div className="relative">
                        <Briefcase className="absolute left-3 top-3 h-5 w-5 text-zinc-500" />
                        <Input 
                          id="role" 
                          value={profile.desired_role}
                          onChange={(e) => setProfile({ ...profile, desired_role: e.target.value })}
                          placeholder="Ej: Senior Frontend Developer, Fullstack Engineer..." 
                          className="pl-10 bg-black/20 border-white/10 text-white placeholder:text-zinc-600 focus-visible:ring-indigo-500"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label htmlFor="salary" className="text-zinc-300">Expectativa Salarial Líquida</Label>
                        <div className="relative">
                          <DollarSign className="absolute left-3 top-3 h-5 w-5 text-zinc-500" />
                          <Input 
                            id="salary" 
                            type="text"
                            value={profile.salary_expectation}
                            onChange={(e) => setProfile({ ...profile, salary_expectation: e.target.value })}
                            placeholder="Ej: $2.500.000 CLP" 
                            className="pl-10 bg-black/20 border-white/10 text-white placeholder:text-zinc-600 focus-visible:ring-indigo-500"
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="modality" className="text-zinc-300">Modalidad Preferida</Label>
                        <div className="relative">
                          <Laptop className="absolute left-3 top-3 h-5 w-5 text-zinc-500" />
                          <Input 
                            id="modality" 
                            value={profile.work_modality}
                            onChange={(e) => setProfile({ ...profile, work_modality: e.target.value })}
                            placeholder="Ej: 100% Remoto, Híbrido Santiago" 
                            className="pl-10 bg-black/20 border-white/10 text-white placeholder:text-zinc-600 focus-visible:ring-indigo-500"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="bio" className="text-zinc-300">Resumen Profesional para la IA</Label>
                      <Textarea 
                        id="bio" 
                        value={profile.professional_summary}
                        onChange={(e) => setProfile({ ...profile, professional_summary: e.target.value })}
                        placeholder="Soy un ingeniero de software con 5 años de experiencia especializándome en React, Next.js y ecosistema cloud..." 
                        className="min-h-[120px] bg-black/20 border-white/10 text-white placeholder:text-zinc-600 focus-visible:ring-indigo-500"
                      />
                    </div>
                  </CardContent>
                  <CardFooter className="pt-2 pb-6 px-6">
                    <Button 
                      onClick={handleSave}
                      disabled={saving || loading}
                      className="w-full sm:w-auto px-8 rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white border-0 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 font-bold shadow-[0_0_20px_rgba(139,92,246,0.3)] transition-all duration-300 flex items-center gap-2"
                    >
                      {saving ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Guardando...
                        </>
                      ) : (
                        "Guardar Preferencias"
                      )}
                    </Button>
                  </CardFooter>
                </Card>
                
              </TabsContent>

              <TabsContent value="account">
                <Card className="bg-zinc-900/50 border-white/5 backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-xl text-white">Detalles de la Cuenta</CardTitle>
                    <CardDescription className="text-zinc-400">
                      Administra tus datos de inicio de sesión.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-white">Sesión Autenticada</p>
                        <p className="text-xs text-zinc-400">Autenticación por Magic Link / Supabase</p>
                      </div>
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Activa
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="notifications">
                <Card className="bg-zinc-900/50 border-white/5 backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-xl text-white">Notificaciones y Alertas</CardTitle>
                    <CardDescription className="text-zinc-400">
                      Recibe alertas de postulaciones y avisos de entrevistas.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="py-8 flex flex-col items-center justify-center text-center">
                      <Bell className="h-12 w-12 text-indigo-400/50 mb-3" />
                      <p className="text-zinc-300 font-medium mb-1">Alertas por Email Habilitadas</p>
                      <p className="text-xs text-zinc-500">Recibirás un correo cuando la IA complete la adaptación de tus postulaciones.</p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="billing">
                <Card className="bg-zinc-900/50 border-white/5 backdrop-blur-md relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                    <Zap className="w-48 h-48 text-indigo-500" />
                  </div>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-xl text-white flex items-center gap-2">
                          Suscripción y Créditos
                          <span className="uppercase text-xs font-bold px-3 py-1 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
                            {profile.plan}
                          </span>
                        </CardTitle>
                        <CardDescription className="text-zinc-400 mt-1">
                          Integrado directamente con pagos seguros vía Flow.cl (Webpay, Servipag, BancoEstado).
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-5 rounded-2xl bg-black/40 border border-white/10 space-y-2">
                        <p className="text-xs text-zinc-400 uppercase font-semibold tracking-wider">Plan Actual</p>
                        <p className="text-2xl font-bold text-white capitalize">{profile.plan} Plan</p>
                        <p className="text-xs text-zinc-500">Límite de adaptaciones mensuales: {profile.ai_credits_limit}</p>
                      </div>

                      <div className="p-5 rounded-2xl bg-black/40 border border-white/10 space-y-2">
                        <p className="text-xs text-zinc-400 uppercase font-semibold tracking-wider">Créditos de IA Usados</p>
                        <p className="text-2xl font-bold text-indigo-400">{profile.ai_credits_used} / {profile.ai_credits_limit}</p>
                        <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                          <div 
                            className="bg-indigo-500 h-full rounded-full transition-all duration-500" 
                            style={{ width: `${Math.min(100, (profile.ai_credits_used / profile.ai_credits_limit) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="border border-indigo-500/30 rounded-2xl p-6 bg-indigo-500/5 relative">
                      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <Zap className="h-5 w-5 text-indigo-400" />
                            <h3 className="text-lg font-bold text-white">HuntJob Pro — $9.900 CLP / mes</h3>
                          </div>
                          <p className="text-sm text-zinc-400">
                            Obtén 100 adaptaciones de CV con IA al mes, simulador ilimitado de entrevistas y soporte prioritario.
                          </p>
                        </div>
                        <Button
                          onClick={() => handleUpgradeFlow("pro")}
                          disabled={paymentLoading}
                          className="w-full md:w-auto px-6 py-3 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-bold shadow-lg transition-all flex items-center justify-center gap-2 shrink-0"
                        >
                          {paymentLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Conectando con Flow...
                            </>
                          ) : (
                            <>
                              Pagar con Flow.cl
                              <ExternalLink className="h-4 w-4" />
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

            </div>
          </Tabs>
        </motion.div>
      </motion.div>
    </div>
  );
}
