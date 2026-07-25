"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createClient } from "@/utils/supabase/client";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const supabase = createClient();

  const handleOAuthLogin = async (provider: "google" | "github" | "facebook") => {
    setLoading(true);
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${location.origin}/auth/callback`,
      },
    });

    if (error) {
      setMessage(`Error: ${error.message}`);
      setLoading(false);
    }
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${location.origin}/auth/callback`,
      },
    });

    if (error) {
      setMessage(`Error: ${error.message}`);
    } else {
      setMessage("Revisa tu correo para el enlace de acceso.");
    }
    setLoading(false);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-screen px-4 py-12 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none" />
      
      <div className="w-full max-w-md relative z-10 space-y-8">
        <div className="text-center">
          <Link href="/" className="inline-flex items-center text-sm font-medium text-zinc-400 hover:text-white transition-colors mb-8">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Volver al inicio
          </Link>
          <h2 className="text-3xl font-heading font-bold tracking-tight text-white">
            Iniciar Sesión
          </h2>
          <p className="mt-2 text-sm text-zinc-400">
            Accede a tu cuenta de HuntJob Pro
          </p>
        </div>

        <div className="bg-zinc-900/50 border border-white/5 p-8 rounded-2xl backdrop-blur-xl shadow-2xl">
          {message && (
            <div className="mb-4 p-3 bg-white/10 border border-white/10 rounded-lg text-sm text-white text-center backdrop-blur-md">
              {message}
            </div>
          )}

          <div className="space-y-4">
            <Button 
              onClick={() => handleOAuthLogin("google")}
              disabled={loading}
              variant="outline" 
              className="w-full h-12 bg-white text-black hover:bg-zinc-200 border-transparent font-medium transition-colors disabled:opacity-50"
            >
              <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
              </svg>
              Continuar con Google
            </Button>
            
            <Button 
              onClick={() => handleOAuthLogin("github")}
              disabled={loading}
              variant="outline" 
              className="w-full h-12 bg-black hover:bg-zinc-900 border-white/10 text-white font-medium transition-colors disabled:opacity-50"
            >
              <svg className="mr-2 h-5 w-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
              Continuar con GitHub
            </Button>
            
            <Button 
              onClick={() => handleOAuthLogin("facebook")}
              disabled={loading}
              variant="outline" 
              className="w-full h-12 bg-[#1877F2] hover:bg-[#0C63D4] border-transparent text-white font-medium transition-colors disabled:opacity-50"
            >
              <svg className="mr-2 h-5 w-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path fillRule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clipRule="evenodd" />
              </svg>
              Continuar con Facebook
            </Button>
          </div>

          <div className="mt-8 flex items-center justify-center">
            <div className="w-full border-t border-white/10" />
            <div className="absolute bg-[#121214] px-4 text-xs uppercase text-zinc-500 tracking-wider">
              O continuar con
            </div>
          </div>

          <form onSubmit={handleEmailLogin} className="mt-8 space-y-4">
            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium text-zinc-300">
                Correo Electrónico
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nombre@ejemplo.com"
                required
                className="w-full h-12 px-4 bg-black/50 border border-white/10 rounded-lg text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-transparent transition-all"
              />
            </div>
            <Button 
              type="submit"
              disabled={loading || !email}
              className="w-full h-12 bg-white text-black hover:bg-zinc-200 font-bold transition-colors disabled:opacity-50"
            >
              <Mail className="mr-2 h-4 w-4" />
              {loading ? "Procesando..." : "Continuar con Email"}
            </Button>
          </form>
        </div>
        
        <p className="text-center text-xs text-zinc-500">
          Al iniciar sesión, aceptas nuestros <Link href="/terms" className="underline hover:text-zinc-300 transition-colors">Términos de Servicio</Link> y <Link href="/privacy" className="underline hover:text-zinc-300 transition-colors">Política de Privacidad</Link>.
        </p>
      </div>
    </div>
  );
}
