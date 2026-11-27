-- Guardian Hub: schema condiviso (Supabase / Postgres 15+).
-- Eseguire una volta in Supabase -> SQL Editor. Idempotente dove possibile.
-- Nessuna credenziale qui dentro: i 3 collaboratori si aggiungono con l'INSERT in fondo (email reali solo nel DB).

create table if not exists public.users (
  id text primary key,                      -- menotti, amico1, amico2 (come registro/persone.json)
  nome text not null,
  email text unique,                        -- email dell'account Supabase Auth
  ruolo text,
  agente text,
  stato text not null default 'attivo' check (stato in ('attivo','sospeso'))
);

create table if not exists public.devices (
  id bigint generated always as identity primary key,
  user_id text not null references public.users(id),
  nome text not null,
  agent_name text,
  model text,
  stato text not null default 'offline' check (stato in ('online','occupato','limite','errore','offline')),
  current_task_id bigint,
  error text,
  limit_reached boolean not null default false,
  last_seen timestamptz,
  last_checkpoint timestamptz,
  token_hash text unique not null,          -- sha256 del token del bridge: il token in chiaro non è mai salvato
  created_at timestamptz not null default now()
);

create table if not exists public.tasks (
  id bigint generated always as identity primary key,
  titolo text not null,
  descrizione text,
  responsabile text references public.users(id),
  agente text,
  priorita text not null default 'media' check (priorita in ('bassa','media','alta','urgente')),
  stato text not null default 'in attesa' check (stato in ('in attesa','in corso','bloccato','completato')),
  next_step text,
  files_changed text[] not null default '{}',
  created_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.activity_events (
  id bigint generated always as identity primary key,
  task_id bigint references public.tasks(id) on delete set null,
  device_id bigint references public.devices(id) on delete set null,
  user_id text,
  agent_name text,
  event_type text not null,
  message text not null,
  files text[] not null default '{}',
  external_key text unique,                 -- idempotenza (es. righe del registro git)
  timestamp timestamptz not null default now()
);

create table if not exists public.handoffs (
  id bigint generated always as identity primary key,
  task_id bigint references public.tasks(id) on delete set null,
  device_id bigint references public.devices(id) on delete set null,
  agent_name text not null,
  summary text not null,
  completed_steps text,
  files_changed text[] not null default '{}',
  decisions text,
  errors text,
  tests text,
  next_step text not null,
  timestamp timestamptz not null default now()
);

create table if not exists public.approvals (
  id bigint generated always as identity primary key,
  task_id bigint references public.tasks(id) on delete set null,
  action text not null,
  description text,
  status text not null default 'richiesta' check (status in ('richiesta','approvata','rifiutata')),
  requested_by text,
  decided_by text,
  created_at timestamptz not null default now(),
  decided_at timestamptz
);

alter table public.devices drop constraint if exists devices_current_task_fk;
alter table public.devices add constraint devices_current_task_fk
  foreign key (current_task_id) references public.tasks(id) on delete set null;

create index if not exists idx_events_ts on public.activity_events (timestamp desc);
create index if not exists idx_tasks_stato on public.tasks (stato);
create index if not exists idx_handoffs_task on public.handoffs (task_id);

-- updated_at automatico
create or replace function public.tocca_updated_at() returns trigger language plpgsql as $$
begin new.updated_at := now(); return new; end $$;
drop trigger if exists tasks_updated_at on public.tasks;
create trigger tasks_updated_at before update on public.tasks for each row execute function public.tocca_updated_at();

-- ---------------------------------------------------------------- accesso
-- Solo gli account la cui email è in public.users (stato attivo) vedono e scrivono.
create or replace function public.is_member() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.users u
                 where lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', '')) and u.stato = 'attivo');
$$;

alter table public.users enable row level security;
alter table public.devices enable row level security;
alter table public.tasks enable row level security;
alter table public.activity_events enable row level security;
alter table public.handoffs enable row level security;
alter table public.approvals enable row level security;

drop policy if exists membri_leggono on public.users;
create policy membri_leggono on public.users for select to authenticated using (public.is_member());
-- users si modifica solo dal SQL Editor (nessuna policy di scrittura).

do $$ declare t text; begin
  foreach t in array array['devices','tasks','activity_events','handoffs','approvals'] loop
    execute format('drop policy if exists membri_tutto on public.%I', t);
    execute format('create policy membri_tutto on public.%I for all to authenticated using (public.is_member()) with check (public.is_member())', t);
  end loop;
end $$;

-- Nessun accesso diretto alle tabelle per "anon" (il bridge usa solo le funzioni RPC qui sotto).
revoke all on public.users, public.devices, public.tasks, public.activity_events, public.handoffs, public.approvals from anon;
-- token_hash non leggibile neppure dai membri.
revoke select on public.devices from authenticated;
grant select (id, user_id, nome, agent_name, model, stato, current_task_id, error, limit_reached, last_seen,
              last_checkpoint, created_at) on public.devices to authenticated;

-- ---------------------------------------------------------------- RPC del Guardian Bridge
create or replace function public._device_da_token(p_token text) returns public.devices
language plpgsql stable security definer set search_path = public as $$
declare d public.devices;
begin
  select * into d from public.devices where token_hash = encode(sha256(convert_to(coalesce(p_token,''), 'UTF8')), 'hex');
  if d.id is null then raise exception 'Token dispositivo non valido' using errcode = '28000'; end if;
  return d;
end $$;

create or replace function public.bridge_heartbeat(p_token text, p_stato text default 'online', p_agent_name text default null,
  p_model text default null, p_current_task bigint default null, p_error text default null, p_limit_reached boolean default false)
returns json language plpgsql security definer set search_path = public as $$
declare d public.devices; prima text;
begin
  d := public._device_da_token(p_token); prima := d.stato;
  update public.devices set stato = p_stato, agent_name = coalesce(nullif(p_agent_name,''), agent_name),
    model = coalesce(nullif(p_model,''), model), current_task_id = p_current_task, error = nullif(left(p_error,500),''),
    limit_reached = coalesce(p_limit_reached,false), last_seen = now()
  where id = d.id returning * into d;
  if prima is distinct from p_stato or p_limit_reached or coalesce(p_error,'') <> '' then
    insert into public.activity_events (task_id, device_id, user_id, agent_name, event_type, message)
    values (p_current_task, d.id, d.user_id, d.agent_name, 'stato_dispositivo',
            d.nome || ': ' || p_stato || case when p_limit_reached then ' (limite raggiunto)' else '' end
                   || case when coalesce(p_error,'') <> '' then ' — ' || left(p_error,300) else '' end);
  end if;
  return json_build_object('id', d.id, 'nome', d.nome, 'user_id', d.user_id, 'stato', d.stato, 'last_seen', d.last_seen);
end $$;

create or replace function public.bridge_event(p_token text, p_event_type text, p_message text, p_task_id bigint default null,
  p_files text[] default '{}', p_external_key text default null)
returns boolean language plpgsql security definer set search_path = public as $$
declare d public.devices; n int;
begin
  d := public._device_da_token(p_token);
  insert into public.activity_events (task_id, device_id, user_id, agent_name, event_type, message, files, external_key)
  values (p_task_id, d.id, d.user_id, d.agent_name, left(p_event_type,40), left(p_message,1000), coalesce(p_files,'{}'), p_external_key)
  on conflict (external_key) do nothing;
  get diagnostics n = row_count; return n > 0;
end $$;

create or replace function public.bridge_task_update(p_token text, p_task_id bigint, p_stato text default null,
  p_next_step text default null, p_files text[] default null)
returns json language plpgsql security definer set search_path = public as $$
declare d public.devices; t public.tasks;
begin
  d := public._device_da_token(p_token);
  update public.tasks set stato = coalesce(nullif(p_stato,''), stato), next_step = coalesce(nullif(p_next_step,''), next_step),
    files_changed = case when p_files is null or cardinality(p_files) = 0 then files_changed else p_files end
  where id = p_task_id returning * into t;
  if t.id is null then raise exception 'Task inesistente'; end if;
  insert into public.activity_events (task_id, device_id, user_id, agent_name, event_type, message, files)
  values (t.id, d.id, d.user_id, d.agent_name, 'task_aggiornato',
          'Task #' || t.id || ' aggiornato: stato=' || t.stato, coalesce(p_files,'{}'));
  return row_to_json(t);
end $$;

create or replace function public.bridge_checkpoint(p_token text, p_summary text, p_next_step text, p_task_id bigint default null,
  p_agent_name text default null, p_completed_steps text default null, p_files_changed text[] default '{}',
  p_decisions text default null, p_errors text default null, p_tests text default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare d public.devices; hid bigint; agente text;
begin
  d := public._device_da_token(p_token);
  agente := coalesce(nullif(p_agent_name,''), d.agent_name, d.nome);
  insert into public.handoffs (task_id, device_id, agent_name, summary, completed_steps, files_changed, decisions, errors, tests, next_step)
  values (p_task_id, d.id, agente, p_summary, p_completed_steps, coalesce(p_files_changed,'{}'), p_decisions, p_errors, p_tests, p_next_step)
  returning id into hid;
  if p_task_id is not null then update public.tasks set next_step = p_next_step where id = p_task_id; end if;
  update public.devices set last_checkpoint = now() where id = d.id;
  insert into public.activity_events (task_id, device_id, user_id, agent_name, event_type, message, files)
  values (p_task_id, d.id, d.user_id, agente, 'checkpoint', 'Handoff salvato. Prossimo passo: ' || left(p_next_step,500),
          coalesce(p_files_changed,'{}'));
  return hid;
end $$;

create or replace function public.bridge_pull_tasks(p_token text)
returns setof public.tasks language plpgsql stable security definer set search_path = public as $$
declare d public.devices;
begin
  d := public._device_da_token(p_token);
  return query select * from public.tasks where responsabile = d.user_id and stato in ('in attesa','in corso','bloccato')
    order by case priorita when 'urgente' then 0 when 'alta' then 1 when 'media' then 2 else 3 end, updated_at desc;
end $$;

-- p_rows: [{"chi","agente","azione","file":[...],"esito","ts","external_key"}] dalle righe di registro/*.jsonl
create or replace function public.bridge_import_registro(p_token text, p_rows jsonb)
returns int language plpgsql security definer set search_path = public as $$
declare r jsonb; n int := 0; k int;
begin
  perform public._device_da_token(p_token);
  for r in select * from jsonb_array_elements(coalesce(p_rows,'[]'::jsonb)) loop
    if exists (select 1 from public.users where id = r->>'chi') then
      insert into public.activity_events (user_id, agent_name, event_type, message, files, external_key, timestamp)
      values (r->>'chi', nullif(r->>'agente',''), 'registro',
              left(coalesce(r->>'azione','') || case when coalesce(r->>'esito','') <> '' then ' [' || (r->>'esito') || ']' else '' end, 1000),
              coalesce((select array_agg(x) from jsonb_array_elements_text(coalesce(r->'file','[]'::jsonb)) x), '{}'),
              r->>'external_key', coalesce((r->>'ts')::timestamptz, now()))
      on conflict (external_key) do nothing;
      get diagnostics k = row_count; n := n + k;
    end if;
  end loop;
  return n;
end $$;

revoke all on function public._device_da_token(text) from public, anon, authenticated;
grant execute on function public.bridge_heartbeat(text,text,text,text,bigint,text,boolean),
  public.bridge_event(text,text,text,bigint,text[],text), public.bridge_task_update(text,bigint,text,text,text[]),
  public.bridge_checkpoint(text,text,text,bigint,text,text,text[],text,text,text), public.bridge_pull_tasks(text),
  public.bridge_import_registro(text,jsonb) to anon, authenticated;

-- ---------------------------------------------------------------- realtime (opzionale)
do $$ begin
  alter publication supabase_realtime add table public.activity_events, public.tasks, public.devices;
exception when others then null; end $$;

-- ---------------------------------------------------------------- collaboratori (MODIFICARE le email prima di eseguire)
-- insert into public.users (id, nome, email, ruolo, agente) values
--   ('menotti', 'Menotti', 'email-di-menotti@example.com', 'Siti, test, software, dashboard', 'Claude Code'),
--   ('amico1', 'nikoopusce7-bit', 'email-amico1@example.com', 'Vendite e dati clienti', 'Codex'),
--   ('amico2', 'Amico 2', 'email-amico2@example.com', 'Amministrazione', 'Codex')
-- on conflict (id) do update set nome = excluded.nome, email = excluded.email, ruolo = excluded.ruolo, agente = excluded.agente;
