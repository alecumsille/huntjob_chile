import { Metadata } from "next";
import { redirect } from "next/navigation";
import { Users, Search, ShieldCheck } from "lucide-react";
import { createClient } from "@supabase/supabase-js";
import { createClient as createServerClient } from "@/utils/supabase/server";

export const metadata: Metadata = {
  title: "Usuarios | HuntJob Pro",
  description: "Administración de usuarios registrados.",
};

// Evita que Next.js cachee esta página estáticamente
export const dynamic = 'force-dynamic';

const ADMIN_EMAILS = ["alecumsille@gmail.com", "ale@cumsille.tech"];

export default async function UsersPage() {
  const supabase = await createServerClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user || !user.email || !ADMIN_EMAILS.includes(user.email)) {
    redirect("/dashboard");
  }

  // Crear el cliente de Supabase usando el Service Role Key para acceder a auth.users
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
  
  const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  });

  const { data, error } = await supabaseAdmin.auth.admin.listUsers();
  const users = data?.users || [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-white mb-2 flex items-center gap-2">
            <Users className="w-8 h-8 text-indigo-400" />
            Usuarios Registrados
          </h1>
          <p className="text-zinc-400 text-sm">
            Gestiona la lista de usuarios que tienen acceso a la plataforma.
          </p>
        </div>
        <div className="bg-green-500/10 border border-green-500/20 px-4 py-2 rounded-full flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-green-400" />
          <span className="text-green-400 text-sm font-medium">Conexión Segura Activa</span>
        </div>
      </div>

      <div className="bg-zinc-900/50 border border-white/5 rounded-2xl overflow-hidden backdrop-blur-xl">
        <div className="p-4 border-b border-white/5 flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input 
              type="text" 
              placeholder="Buscar usuarios (pronto)..." 
              disabled
              className="w-full bg-black/50 border border-white/10 rounded-lg py-2 pl-10 pr-4 text-sm text-white placeholder:text-zinc-600 focus:outline-none opacity-50 cursor-not-allowed"
            />
          </div>
          <div className="text-sm text-zinc-500">
            Total: <strong className="text-white">{users.length}</strong> usuarios
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-black/20 text-zinc-400 text-xs uppercase tracking-wider">
                <th className="p-4 font-medium">Email</th>
                <th className="p-4 font-medium">Proveedor</th>
                <th className="p-4 font-medium">Último Acceso</th>
                <th className="p-4 font-medium">Fecha de Registro</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {error && (
                <tr>
                  <td colSpan={4} className="p-8 text-center text-red-400">
                    Error al cargar los usuarios: {error.message}
                  </td>
                </tr>
              )}
              
              {!error && users.length === 0 && (
                <tr>
                  <td colSpan={4} className="p-8 text-center text-zinc-500">
                    No hay usuarios registrados todavía.
                  </td>
                </tr>
              )}

              {users.map((user) => (
                <tr key={user.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-sm">
                        {user.email?.[0].toUpperCase()}
                      </div>
                      <span className="text-zinc-200 font-medium">{user.email}</span>
                    </div>
                  </td>
                  <td className="p-4 text-zinc-400 text-sm">
                    {user.app_metadata.provider || 'email'}
                  </td>
                  <td className="p-4 text-zinc-400 text-sm">
                    {user.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td className="p-4 text-zinc-400 text-sm">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
