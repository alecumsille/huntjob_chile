-- HuntJob Chile — esquema de datos por usuario en Supabase Postgres.
-- Ejecutar una sola vez en: Supabase Dashboard > SQL Editor > New query.
--
-- Reemplaza el YAML/SQLite local compartido (que filtraba datos entre
-- visitantes) por tablas con Row Level Security: cada usuario solo puede
-- leer/escribir sus propias filas, verificado por Postgres mismo — no
-- por la app. No requiere Service Role Key en ningún momento.

create table if not exists public.perfiles (
    user_id uuid primary key references auth.users(id) on delete cascade,
    nombre text default '',
    email text default '',
    telefono text default '',
    linkedin text default '',
    anos_experiencia integer default 0,
    seniority text default 'Junior',
    stack_principal text default '',
    logros_y_experiencia text default '',
    actualizado_en timestamptz default now()
);

create table if not exists public.historial_postulaciones (
    id bigint generated always as identity primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    puesto text,
    empresa text,
    mercado text,
    url_oferta text,
    cv_texto text,
    cover_letter_texto text,
    estilo_pdf text,
    match_score integer,
    estado text default 'generado', -- generado | postulado
    creado_en timestamptz default now()
);

create table if not exists public.planes_usuario (
    user_id uuid primary key references auth.users(id) on delete cascade,
    plan text not null default 'free', -- free | premium
    limite_mensual integer not null default 5,
    generaciones_este_mes integer not null default 0,
    periodo text not null default to_char(now(), 'YYYY-MM'),
    creado_en timestamptz default now()
);

alter table public.perfiles enable row level security;
alter table public.historial_postulaciones enable row level security;
alter table public.planes_usuario enable row level security;

drop policy if exists "perfiles_propio" on public.perfiles;
create policy "perfiles_propio" on public.perfiles
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "historial_propio" on public.historial_postulaciones;
create policy "historial_propio" on public.historial_postulaciones
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "plan_propio" on public.planes_usuario;
create policy "plan_propio" on public.planes_usuario
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Crea automáticamente la fila de plan (free) apenas se registra un
-- usuario nuevo vía OAuth, para que verificar_y_consumir_uso() nunca
-- tenga que manejar "usuario sin plan todavía" como caso especial.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.planes_usuario (user_id) values (new.id)
    on conflict (user_id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();

-- Suscripcion Premium via Flow.cl (2026-07-22)
alter table public.planes_usuario
    add column if not exists flow_customer_id text unique,
    add column if not exists plan_vence_en timestamptz;
