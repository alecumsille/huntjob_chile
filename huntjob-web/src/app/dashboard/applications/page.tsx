"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/utils/supabase/client";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus, Briefcase, Calendar, Building, Search, ArrowRight, Filter } from "lucide-react";

interface Application {
  id: string;
  company_name: string;
  job_title: string;
  status: 'pending' | 'interview_scheduled' | 'rejected' | 'offer';
  applied_at: string;
  notes?: string;
}

const mockApplications: Application[] = [
  {
    id: '1',
    company_name: 'TechNova',
    job_title: 'Senior Frontend Engineer',
    status: 'interview_scheduled',
    applied_at: '2024-07-20T10:00:00Z',
    notes: 'Primera entrevista técnica el martes.'
  },
  {
    id: '2',
    company_name: 'Acme Corp',
    job_title: 'Full Stack Developer',
    status: 'pending',
    applied_at: '2024-07-22T14:30:00Z',
  },
  {
    id: '3',
    company_name: 'Global Solutions',
    job_title: 'React Native Developer',
    status: 'rejected',
    applied_at: '2024-07-15T09:15:00Z',
  },
  {
    id: '4',
    company_name: 'StartupX',
    job_title: 'Lead Software Engineer',
    status: 'offer',
    applied_at: '2024-07-10T16:45:00Z',
    notes: 'Oferta inicial $120k, intentar negociar.'
  }
];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  
  // Form state
  const [newApp, setNewApp] = useState({ company_name: '', job_title: '', status: 'pending' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const supabase = createClient();



  const fetchApplications = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('applications')
        .select('*')
        .order('applied_at', { ascending: false });
        
      if (error || !data || data.length === 0) {
        // Fallback a datos mockeados si no existe la tabla o está vacía
        setApplications(mockApplications);
      } else {
        setApplications(data as Application[]);
      }
    } catch (err) {
      console.error(err);
      setApplications(mockApplications);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps, react-hooks/set-state-in-effect
    fetchApplications();
  }, []);

  const getStatusBadge = (status: Application['status']) => {
    switch (status) {
      case 'pending': return <Badge variant="outline" className="border-amber-500/30 bg-amber-500/10 text-amber-500">En revisión</Badge>;
      case 'interview_scheduled': return <Badge variant="outline" className="border-indigo-500/30 bg-indigo-500/10 text-indigo-400">Entrevista</Badge>;
      case 'rejected': return <Badge variant="outline" className="border-rose-500/30 bg-rose-500/10 text-rose-400">Rechazado</Badge>;
      case 'offer': return <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400">Oferta</Badge>;
      default: return null;
    }
  };

  const filteredApps = applications.filter(app => 
    app.company_name.toLowerCase().includes(search.toLowerCase()) ||
    app.job_title.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreateApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newApp.company_name || !newApp.job_title) return;
    setIsSubmitting(true);
    
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data, error } = await supabase
        .from('applications')
        .insert([{
          user_id: user.id,
          company_name: newApp.company_name,
          job_title: newApp.job_title,
          status: newApp.status
        }])
        .select()
        .single();
        
      if (!error && data) {
        setApplications([data, ...applications]);
        setShowForm(false);
        setNewApp({ company_name: '', job_title: '', status: 'pending' });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-white tracking-tight">Postulaciones</h1>
          <p className="text-zinc-400 mt-1">Gestiona tu funnel de entrevistas y ofertas.</p>
        </div>
        <Button 
          onClick={() => setShowForm(!showForm)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 border-0 rounded-xl"
        >
          {showForm ? 'Cancelar' : <><Plus className="mr-2 h-4 w-4" /> Nueva Postulación</>}
        </Button>
      </div>

      {showForm && (
        <Card className="bg-zinc-900/60 border-white/10 mb-8 p-6">
          <form onSubmit={handleCreateApplication} className="grid gap-4 sm:grid-cols-4 items-end">
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Empresa</label>
              <input 
                value={newApp.company_name}
                onChange={e => setNewApp({...newApp, company_name: e.target.value})}
                placeholder="Ej. TechNova"
                className="w-full bg-black/50 border border-white/10 rounded-lg p-2.5 text-white text-sm" 
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Puesto</label>
              <input 
                value={newApp.job_title}
                onChange={e => setNewApp({...newApp, job_title: e.target.value})}
                placeholder="Ej. Frontend Eng"
                className="w-full bg-black/50 border border-white/10 rounded-lg p-2.5 text-white text-sm" 
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Estado inicial</label>
              <select 
                value={newApp.status}
                onChange={e => setNewApp({...newApp, status: e.target.value})}
                className="w-full bg-black/50 border border-white/10 rounded-lg p-2.5 text-white text-sm"
              >
                <option value="pending">En revisión</option>
                <option value="interview_scheduled">Entrevista</option>
                <option value="offer">Oferta</option>
                <option value="rejected">Rechazado</option>
              </select>
            </div>
            <Button disabled={isSubmitting} type="submit" className="bg-emerald-600 hover:bg-emerald-500 text-white h-[42px] rounded-lg">
              Guardar Postulación
            </Button>
          </form>
        </Card>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <input 
            type="text" 
            placeholder="Buscar empresa o rol..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-zinc-900 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all"
          />
        </div>
        <Button variant="outline" className="border-white/10 bg-zinc-900 hover:bg-white/5 text-white rounded-xl h-[38px]">
          <Filter className="mr-2 h-4 w-4 text-zinc-400" />
          Filtros
        </Button>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          // Loading skeletons
          Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="bg-zinc-900/50 border-white/5 animate-pulse">
              <CardContent className="p-6 h-48"></CardContent>
            </Card>
          ))
        ) : (
          filteredApps.map((app) => (
            <Card key={app.id} className="bg-zinc-900/40 border-white/10 hover:border-indigo-500/30 hover:bg-zinc-900/60 transition-all duration-300 group cursor-pointer overflow-hidden relative">
              <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-indigo-500 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity" />
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-white font-bold">
                      {app.company_name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">{app.company_name}</h3>
                      <div className="flex items-center gap-1.5 text-xs text-zinc-500 mt-0.5">
                        <Briefcase className="w-3 h-3" />
                        {app.job_title}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between mt-6">
                  {getStatusBadge(app.status)}
                  
                  <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                    <Calendar className="w-3 h-3" />
                    {new Date(app.applied_at).toLocaleDateString('es-ES', { month: 'short', day: 'numeric' })}
                  </div>
                </div>

                <div className="mt-5 pt-5 border-t border-white/5 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity translate-y-2 group-hover:translate-y-0">
                  <span className="text-xs text-zinc-400 font-medium">Ver detalles</span>
                  <ArrowRight className="w-4 h-4 text-indigo-400" />
                </div>
              </CardContent>
            </Card>
          ))
        )}
        
        {!loading && filteredApps.length === 0 && (
          <div className="col-span-full py-12 text-center border border-dashed border-white/10 rounded-xl bg-zinc-900/20">
            <Building className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
            <p className="text-zinc-400 text-sm">No se encontraron postulaciones</p>
          </div>
        )}
      </div>
    </div>
  );
}
