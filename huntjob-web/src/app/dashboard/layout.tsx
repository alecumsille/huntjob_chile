"use client";

import { createClient } from "@/utils/supabase/client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Settings,
  LogOut,
  Bell,
  Search,
  Menu,
  ClipboardCheck,
} from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const supabase = createClient();
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        setUserEmail(user.email ?? "Usuario Pro");
      }
    };
    getUser();
  }, [supabase.auth]);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push("/auth/login");
    router.refresh();
  };

  const navItems = [
    { icon: LayoutDashboard, label: "Resumen", href: "/dashboard" },
    { icon: Briefcase, label: "Postulaciones", href: "/dashboard/applications" },
    { icon: FileText, label: "Currículums", href: "/dashboard/resumes" },
    { icon: ClipboardCheck, label: "Evaluar Oferta", href: "/dashboard/evaluate" },
    { icon: Settings, label: "Configuración", href: "/dashboard/settings" },
  ];

  return (
    <div className="flex h-screen bg-black overflow-hidden">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex w-72 flex-col bg-zinc-950 border-r border-white/10 z-20">
        <div className="h-20 flex items-center px-8 border-b border-white/10">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="h-8 w-8 bg-white rounded-lg flex items-center justify-center">
              <div className="w-4 h-4 bg-black rounded-sm" />
            </div>
            <span className="text-xl font-heading font-bold text-white tracking-tight">
              HuntJob <span className="text-zinc-500">Pro</span>
            </span>
          </Link>
        </div>

        <div className="flex-1 overflow-y-auto py-8 px-4 space-y-2">
          <div className="px-4 mb-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            Menú Principal
          </div>
          {navItems.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                item.href === "/dashboard"
                  ? "bg-white/10 text-white font-medium"
                  : "text-zinc-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <item.icon className={`h-5 w-5 ${item.href === "/dashboard" ? "text-indigo-400" : ""}`} />
              {item.label}
            </Link>
          ))}
        </div>

        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3 px-4 py-3 bg-zinc-900 rounded-xl border border-white/5 mb-2">
            <div className="h-10 w-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold">
              {userEmail ? userEmail.charAt(0).toUpperCase() : "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {userEmail || "Cargando..."}
              </p>
              <p className="text-xs text-emerald-400">Plan Pro Activo</p>
            </div>
          </div>
          <button
            onClick={handleSignOut}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Cerrar Sesión
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Glow effect */}
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none" />
        
        {/* Top Header */}
        <header className="h-20 flex items-center justify-between px-6 lg:px-10 border-b border-white/10 bg-zinc-950/50 backdrop-blur-md z-10">
          <div className="flex items-center gap-4 lg:hidden">
            <button className="text-zinc-400 hover:text-white">
              <Menu className="h-6 w-6" />
            </button>
          </div>
          
          <div className="hidden lg:flex items-center flex-1 max-w-xl">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
              <input 
                type="text" 
                placeholder="Buscar vacantes, empresas..." 
                className="w-full bg-white/5 border border-white/10 rounded-full py-2.5 pl-10 pr-4 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="relative p-2 text-zinc-400 hover:text-white transition-colors rounded-full hover:bg-white/5">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1.5 right-2 w-2 h-2 bg-indigo-500 rounded-full border-2 border-black" />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-10 z-10 relative">
          {children}
        </main>
      </div>
    </div>
  );
}
