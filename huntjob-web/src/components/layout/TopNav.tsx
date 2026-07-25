"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Briefcase, LayoutDashboard, Settings } from "lucide-react";

export function TopNav() {
  const pathname = usePathname();

  const navItems = [
    { name: "Características", href: "/features", icon: Briefcase },
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Configuración", href: "/settings", icon: Settings },
  ];

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-white/5 bg-black/40 backdrop-blur-xl">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-900 border border-white/10 shadow-lg transition-shadow">
                <Briefcase className="h-4 w-4 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight text-white/90 group-hover:text-white transition-colors">
                HuntJob <span className="text-zinc-400 font-light">Pro</span>
              </span>
            </Link>
          </div>
          <div className="hidden md:block">
            <div className="ml-10 flex items-center space-x-1">
              {navItems.map((item) => {
                const isActive = pathname.startsWith(item.href);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`relative px-4 py-2 text-sm font-medium transition-colors ${
                      isActive ? "text-white" : "text-zinc-400 hover:text-white"
                    }`}
                  >
                    <span className="flex items-center gap-2 relative z-10">
                      <Icon className="h-4 w-4" />
                      {item.name}
                    </span>
                    {isActive && (
                      <motion.div
                        layoutId="nav-active"
                        className="absolute inset-0 rounded-full bg-white/10 shadow-inner"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.3 }}
                      />
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
          <div>
            <Link
              href="/auth/login"
              className="px-4 py-2 text-sm font-medium text-white bg-white/10 hover:bg-white/20 rounded-full border border-white/5 transition-all"
            >
              Iniciar Sesión
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
