-- Guardian 002 — NEXO AI Command Center: progetti, agenti, piani, log, notifiche, memoria;
-- task con 10 stati, dipendenze e vincoli anti-duplicato; gravità degli eventi; approvazioni dettagliate.
-- Additiva e compatibile con i dati di 001 (gli stati dei task vengono convertiti). Rieseguibile.

-- ---------------------------------------------------------------- utenti: livello di accesso
alter table public.users add column if not exists accesso text not null default 'member';
alter table public.users drop constraint if exists users_accesso_check;
alter table public.users add constraint users_accesso_check check (accesso in ('admin','member'));

create or replace function public.my_user_id() returns text
language sql stable security definer set search_path = public as $$
  select u.id from public.users u
  where lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', '')) and u.stato = 'attivo';
$$;

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.users u where u.id = public.my_user_id() and u.accesso = 'admin');
$$;

-- ---------------------------------------------------------------- nuove tabelle
create table if not exists public.projects (
  id bigint generated always as identity primary key,
  nome text not null,
  descrizione text,
  stato text not null default 'attivo' check (stato in ('attivo','archiviato')),
  created_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists projects_nome_uniq on public.projects (lower(nome));

create table if not exists public.agents (
  id text primary key,                                   -- es. menotti-claude
  user_id text not null references public.users(id),
  device_id bigint references public.devices(id) on delete set null,
  nome text not null,
  tipo text not null check (tipo in ('claude-code','codex','api','manuale')),
  capabilities text[] not null default '{}',
  stato text not null default 'unknown'
    check (stato in ('online','offline','idle','working','waiting','needs_approval','error','unknown')),
  current_task_id bigint,
  last_heartbeat timestamptz,
  last_activity timestamptz,
  error text,
  disponibile boolean not null default true,
  usage jsonb,                                           -- % utilizzo 5h/7g solo se letto da fonte reale
  created_at timestamptz not null default now()
);

create table if not exists public.plans (
  id bigint generated always as identity primary key,
  goal text not null,
  project_id bigint references public.projects(id) on delete set null,
  provider text,
  model text,
  piano jsonb not null,
  stato text not null default 'bozza' check (stato in ('bozza','confermato','scartato')),
  created_by text,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_logs (
  id bigint generated always as identity primary key,
  agent_id text references public.agents(id) on delete set null,
  device_id bigint references public.devices(id) on delete set null,
  project_id bigint references public.projects(id) on delete set null,
  task_id bigint,
  level text not null default 'info' check (level in ('debug','info','warning','error')),
  source text not null,                                  -- hook | notify | bridge
  message text not null,                                 -- metadati + prompt troncati (mai output dei tool)
  ts timestamptz not null default now()
);
create index if not exists idx_logs_ts on public.agent_logs (ts desc);
create index if not exists idx_logs_agent on public.agent_logs (agent_id, ts desc);

create table if not exists public.notifications (
  id bigint generated always as identity primary key,
  user_id text not null references public.users(id),
  kind text not null,
  message text not null,
  ref_table text,
  ref_id text,
  read_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists idx_notif_user on public.notifications (user_id, read_at);

create table if not exists public.memory (
  id bigint generated always as identity primary key,
  project_id bigint references public.projects(id) on delete set null,
  task_id bigint references public.tasks(id) on delete set null,
  kind text not null check (kind in ('obiettivo','decisione','info_progetto','preferenza','risultato','errore','procedura','ripresa')),
  content text not null,
  source text not null,                                  -- da dove viene (file, handoff #, conversazione, persona)
  created_by text,
  created_at timestamptz not null default now(),
  superseded_by bigint references public.memory(id),
  ricerca tsvector generated always as (to_tsvector('italian', content)) stored
);
create index if not exists idx_memory_ricerca on public.memory using gin (ricerca);

-- ---------------------------------------------------------------- tasks v2
alter table public.tasks
  add column if not exists project_id bigint references public.projects(id) on delete set null,
  add column if not exists plan_id bigint references public.plans(id) on delete set null,
  add column if not exists assigned_agent_id text references public.agents(id) on delete set null,
  add column if not exists depends_on bigint[] not null default '{}',
  add column if not exists result text,
  add column if not exists error text,
  add column if not exists expected_result text,
  add column if not exists completion_criteria text;

alter table public.tasks drop constraint if exists tasks_stato_check;
update public.tasks set stato = case stato when 'in attesa' then 'ready' when 'in corso' then 'running'
  when 'bloccato' then 'blocked' when 'completato' then 'completed' else stato end;
alter table public.tasks alter column stato set default 'backlog';
alter table public.tasks add constraint tasks_stato_check check (stato in
  ('backlog','planned','ready','running','waiting','blocked','needs_approval','completed','failed','cancelled'));

-- titoli aperti duplicati (ammessi in 001): resi unici prima dell'indice
update public.tasks t set titolo = t.titolo || ' (#' || t.id || ')'
where t.stato not in ('completed','failed','cancelled') and exists (
  select 1 from public.tasks o where o.id < t.id and o.stato not in ('completed','failed','cancelled')
    and coalesce(o.project_id, 0) = coalesce(t.project_id, 0) and lower(o.titolo) = lower(t.titolo));
create unique index if not exists tasks_titolo_aperto on public.tasks (coalesce(project_id, 0), lower(titolo))
  where stato not in ('completed','failed','cancelled');
create unique index if not exists tasks_un_running on public.tasks (assigned_agent_id)
  where stato = 'running' and assigned_agent_id is not null;
create index if not exists idx_tasks_project on public.tasks (project_id);

alter table public.agents drop constraint if exists agents_current_task_fk;
alter table public.agents add constraint agents_current_task_fk
  foreign key (current_task_id) references public.tasks(id) on delete set null;

create or replace function public.tasks_controlla_dipendenze() returns trigger language plpgsql as $$
declare mancanti int; aperte int;
begin
  if new.id = any(new.depends_on) then raise exception 'Un task non può dipendere da sé stesso'; end if;
  if cardinality(new.depends_on) = 0 then return new; end if;
  select cardinality(new.depends_on) - count(*) into mancanti from public.tasks where id = any(new.depends_on);
  if mancanti > 0 then raise exception 'Dipendenze inesistenti'; end if;
  if new.stato in ('ready','running') then
    select count(*) into aperte from public.tasks where id = any(new.depends_on) and stato <> 'completed';
    if aperte > 0 then raise exception 'Il task ha dipendenze non ancora completate'; end if;
  end if;
  return new;
end $$;
drop trigger if exists tasks_dipendenze on public.tasks;
create trigger tasks_dipendenze before insert or update of stato, depends_on on public.tasks
  for each row execute function public.tasks_controlla_dipendenze();

-- ---------------------------------------------------------------- eventi, handoff, approvazioni v2
alter table public.activity_events
  add column if not exists severity text not null default 'info',
  add column if not exists agent_id text,
  add column if not exists project_id bigint;
alter table public.activity_events drop constraint if exists activity_events_severity_check;
alter table public.activity_events add constraint activity_events_severity_check
  check (severity in ('info','warning','error','critical'));

alter table public.handoffs
  add column if not exists from_agent_id text,
  add column if not exists to_agent_id text,
  add column if not exists tests_pending text,
  add column if not exists dependencies text,
  add column if not exists important_notes text,
  add column if not exists stato text not null default 'aperto';
alter table public.handoffs drop constraint if exists handoffs_stato_check;
alter table public.handoffs add constraint handoffs_stato_check check (stato in ('aperto','preso','chiuso'));

alter table public.approvals
  add column if not exists agent_id text,
  add column if not exists action_type text not null default 'altro',
  add column if not exists reason text,
  add column if not exists impact text,
  add column if not exists data_involved text;
alter table public.approvals drop constraint if exists approvals_action_type_check;
alter table public.approvals add constraint approvals_action_type_check check (action_type in
  ('email','pubblicazione','contatto_cliente','spesa','pagamento','irreversibile','account_esterno','comando_pericoloso','altro'));

-- ---------------------------------------------------------------- notifiche e stati automatici (trigger)
create or replace function public.notifica(p_user text, p_kind text, p_msg text, p_table text, p_ref text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_user is null then
    insert into public.notifications (user_id, kind, message, ref_table, ref_id)
    select id, p_kind, left(p_msg, 500), p_table, p_ref from public.users where stato = 'attivo';
  else
    insert into public.notifications (user_id, kind, message, ref_table, ref_id) values (p_user, p_kind, left(p_msg, 500), p_table, p_ref);
  end if;
end $$;
revoke all on function public.notifica(text,text,text,text,text) from public, anon, authenticated;

create or replace function public.approvals_dopo_insert() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.status = 'richiesta' then
    update public.tasks set stato = 'needs_approval'
    where id = new.task_id and stato not in ('completed','failed','cancelled');
    perform public.notifica(null, 'approval_requested', 'Da approvare: ' || new.action, 'approvals', new.id::text);
  end if;
  return new;
end $$;
drop trigger if exists approvals_insert on public.approvals;
create trigger approvals_insert after insert on public.approvals for each row execute function public.approvals_dopo_insert();

create or replace function public.approvals_dopo_decisione() returns trigger
language plpgsql security definer set search_path = public as $$
declare t public.tasks; nuovo text;
begin
  if old.status <> 'richiesta' or new.status = 'richiesta' then return new; end if;
  select * into t from public.tasks where id = new.task_id;
  if t.id is not null and t.stato = 'needs_approval'
     and not exists (select 1 from public.approvals where task_id = t.id and status = 'richiesta' and id <> new.id) then
    nuovo := case when new.status = 'rifiutata' then 'blocked'
                  when exists (select 1 from public.tasks d where d.id = any(t.depends_on) and d.stato <> 'completed') then 'planned'
                  else 'ready' end;
    update public.tasks set stato = nuovo where id = t.id;
  end if;
  if new.requested_by is not null then
    perform public.notifica(new.requested_by, 'approval_decided', new.action || ': ' || new.status, 'approvals', new.id::text);
  end if;
  return new;
end $$;
drop trigger if exists approvals_decisione on public.approvals;
create trigger approvals_decisione after update of status on public.approvals
  for each row execute function public.approvals_dopo_decisione();

create or replace function public.tasks_dopo_update() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.stato = 'failed' and old.stato <> 'failed' then
    perform public.notifica(new.responsabile, 'task_failed', 'Task #' || new.id || ' fallito: ' || new.titolo, 'tasks', new.id::text);
  end if;
  return new;
end $$;
drop trigger if exists tasks_notifiche on public.tasks;
create trigger tasks_notifiche after update of stato on public.tasks for each row execute function public.tasks_dopo_update();

create or replace function public.agents_dopo_update() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.stato = 'error' and old.stato is distinct from 'error' then
    perform public.notifica(new.user_id, 'agent_error', 'Agente ' || new.nome || ' in errore: ' || coalesce(new.error, 'senza dettagli'),
                            'agents', new.id);
  end if;
  return new;
end $$;
drop trigger if exists agents_notifiche on public.agents;
create trigger agents_notifiche after update of stato on public.agents for each row execute function public.agents_dopo_update();

drop trigger if exists projects_updated_at on public.projects;
create trigger projects_updated_at before update on public.projects for each row execute function public.tocca_updated_at();

-- ---------------------------------------------------------------- RPC del bridge aggiornata ai nuovi stati
create or replace function public.bridge_pull_tasks(p_token text)
returns setof public.tasks language plpgsql stable security definer set search_path = public as $$
declare d public.devices;
begin
  d := public._device_da_token(p_token);
  return query select * from public.tasks
    where responsabile = d.user_id and stato in ('planned','ready','running','waiting','blocked','needs_approval')
    order by case priorita when 'urgente' then 0 when 'alta' then 1 when 'media' then 2 else 3 end, updated_at desc;
end $$;

-- pulizia log oltre 30 giorni (da pianificare con pg_cron o eseguire a mano)
create or replace function public.pulisci_log_vecchi(p_giorni int default 30) returns int
language sql security definer set search_path = public as $$
  with x as (delete from public.agent_logs where ts < now() - make_interval(days => p_giorni) returning 1) select count(*)::int from x;
$$;
revoke all on function public.pulisci_log_vecchi(int) from public, anon, authenticated;

-- ---------------------------------------------------------------- accesso (RLS)
alter table public.projects enable row level security;
alter table public.agents enable row level security;
alter table public.plans enable row level security;
alter table public.agent_logs enable row level security;
alter table public.notifications enable row level security;
alter table public.memory enable row level security;

do $$ declare t text; begin
  foreach t in array array['projects','agents','plans','agent_logs','memory'] loop
    execute format('drop policy if exists membri_tutto on public.%I', t);
    execute format('create policy membri_tutto on public.%I for all to authenticated using (public.is_member()) with check (public.is_member())', t);
  end loop;
end $$;

-- notifiche: ognuno vede e segna come lette solo le proprie
drop policy if exists proprie on public.notifications;
create policy proprie on public.notifications for select to authenticated using (user_id = public.my_user_id());
drop policy if exists proprie_lette on public.notifications;
create policy proprie_lette on public.notifications for update to authenticated
  using (user_id = public.my_user_id()) with check (user_id = public.my_user_id());

-- utenti: modifiche solo admin; dispositivi: revoca solo proprietario o admin
drop policy if exists admin_scrive on public.users;
create policy admin_scrive on public.users for update to authenticated using (public.is_admin()) with check (public.is_admin());
drop policy if exists membri_tutto on public.devices;
drop policy if exists membri_leggono on public.devices;
create policy membri_leggono on public.devices for select to authenticated using (public.is_member());
drop policy if exists registra_propri on public.devices;
create policy registra_propri on public.devices for insert to authenticated
  with check (public.is_member() and (user_id = public.my_user_id() or public.is_admin()));
drop policy if exists modifica_propri on public.devices;
create policy modifica_propri on public.devices for update to authenticated
  using (user_id = public.my_user_id() or public.is_admin()) with check (user_id = public.my_user_id() or public.is_admin());

revoke all on public.projects, public.agents, public.plans, public.agent_logs, public.notifications, public.memory from anon;
-- notifications: solo lettura + update di read_at per gli utenti
revoke insert, delete on public.notifications from authenticated;
revoke update on public.notifications from authenticated;
grant update (read_at) on public.notifications to authenticated;

do $$ begin
  alter publication supabase_realtime add table public.agents, public.notifications, public.approvals;
exception when others then null; end $$;

-- Dopo questa migrazione: rendere admin il titolare (dal SQL Editor)
-- update public.users set accesso = 'admin' where id = 'menotti';
