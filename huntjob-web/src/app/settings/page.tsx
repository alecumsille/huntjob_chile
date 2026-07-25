"use client";

import { motion } from "framer-motion";
import { 
  User, 
  Briefcase, 
  Bell, 
  CreditCard,
  UploadCloud,
  FileText,
  MapPin,
  DollarSign,
  Laptop
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

export default function SettingsPage() {
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
          <p className="text-zinc-400">Gestiona tus preferencias, perfil profesional y ajustes de la cuenta.</p>
        </motion.div>

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
                Suscripción
              </TabsTrigger>
            </TabsList>

            <div className="flex-1">
              <TabsContent value="profile" className="mt-0 space-y-6">
                
                <Card className="bg-zinc-900/50 border-white/5 backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-xl text-white">Currículum Base</CardTitle>
                    <CardDescription className="text-zinc-400">
                      Sube tu CV actual. Nuestra IA lo usará de contexto base para generar postulaciones hiper-personalizadas.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="border-2 border-dashed border-white/10 rounded-2xl p-10 flex flex-col items-center justify-center text-center hover:bg-white/5 hover:border-indigo-500/50 transition-all cursor-pointer group">
                      <div className="h-16 w-16 bg-white/5 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                        <UploadCloud className="h-8 w-8 text-indigo-400" />
                      </div>
                      <p className="text-white font-medium mb-1">Haz clic para subir o arrastra tu archivo PDF</p>
                      <p className="text-sm text-zinc-500">Máximo 5MB</p>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-900/50 border-white/5 backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-xl text-white">Preferencias Laborales</CardTitle>
                    <CardDescription className="text-zinc-400">
                      Define qué estás buscando para que el piloto automático sepa a qué postularte.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="role" className="text-zinc-300">Rol o Cargo Deseado</Label>
                      <div className="relative">
                        <Briefcase className="absolute left-3 top-3 h-5 w-5 text-zinc-500" />
                        <Input 
                          id="role" 
                          placeholder="Ej: Senior Frontend Developer, Product Manager..." 
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
                            placeholder="Ej: 100% Remoto, Híbrido" 
                            className="pl-10 bg-black/20 border-white/10 text-white placeholder:text-zinc-600 focus-visible:ring-indigo-500"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="bio" className="text-zinc-300">Resumen Profesional para la IA</Label>
                      <Textarea 
                        id="bio" 
                        placeholder="Soy un ingeniero de software con 5 años de experiencia especializándome en React y ecosistema serverless..." 
                        className="min-h-[120px] bg-black/20 border-white/10 text-white placeholder:text-zinc-600 focus-visible:ring-indigo-500"
                      />
                      <p className="text-xs text-zinc-500">
                        Esta información es fundamental para que la IA redacte cover letters impecables y que suenen a ti.
                      </p>
                    </div>
                  </CardContent>
                  <CardFooter className="pt-2 pb-6 px-6">
                    <Button 
                      className="w-full sm:w-auto px-8 rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white border-0 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 font-bold shadow-[0_0_20px_rgba(139,92,246,0.3)] transition-all duration-300"
                    >
                      Guardar Preferencias
                    </Button>
                  </CardFooter>
                </Card>
                
              </TabsContent>

              {/* Placeholder tabs for future use */}
              <TabsContent value="account">
                <Card className="bg-zinc-900/50 border-white/5 backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-xl text-white">Detalles de la Cuenta</CardTitle>
                    <CardDescription className="text-zinc-400">
                      Administra tu correo electrónico, contraseña y seguridad.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="py-12 flex flex-col items-center justify-center text-center opacity-50">
                      <User className="h-12 w-12 text-zinc-500 mb-4" />
                      <p className="text-zinc-400">Configuración de cuenta próximamente</p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="notifications">
                <Card className="bg-zinc-900/50 border-white/5 backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-xl text-white">Notificaciones y Alertas</CardTitle>
                    <CardDescription className="text-zinc-400">
                      Elige cuándo y cómo quieres que HuntJob te contacte.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="py-12 flex flex-col items-center justify-center text-center opacity-50">
                      <Bell className="h-12 w-12 text-zinc-500 mb-4" />
                      <p className="text-zinc-400">Centro de notificaciones próximamente</p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="billing">
                <Card className="bg-zinc-900/50 border-white/5 backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-xl text-white">Suscripción y Créditos</CardTitle>
                    <CardDescription className="text-zinc-400">
                      Gestiona tu plan HuntJob Pro y tus métodos de pago.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="py-12 flex flex-col items-center justify-center text-center opacity-50">
                      <CreditCard className="h-12 w-12 text-zinc-500 mb-4" />
                      <p className="text-zinc-400">Panel de facturación próximamente</p>
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
