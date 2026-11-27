-- Guardian 003 — RPC del Bridge v2 per gli agenti (stato da eventi reali, log, presa in carico dei task).
-- Tutte validano il token del PC; un PC può gestire solo agenti del proprio collaboratore. Rieseguibile.

create or replace function public._agente_del_device(d public.devices, p_agent_id text) returns public.agents
language plpgsql stable security definer set search_path = public as $$
declare a public.agents;
begin
  select * into a from public.agents where id = lower(p_agent_id);
  if a.id is null then raise exception 'Agente non registrato: %', p_agent_id; end if;
  if a.user_id <> d.user_id then raise exception 'Agente di un altro collaboratore' using errcode = '42501'; end if;
  return a;
end $$;
revoke all on function public._agente_del_device(public.devices, text) from public, anon, authenticated;

create or replace function public.bridge_agent_register(p_token text, p_agent_id text, p_nome text, p_tipo text,
  p_capabilities text[] default '{}')
returns json language plpgsql security definer set search_path = public as $$
declare d public.devices; a public.agents;
begin
  d := public._device_da_token(p_token);
  select * into a from public.agents where id = lower(p_agent_id);
  if a.id is not null and a.user_id <> d.user_id then
    raise exception 'Agente di un altro collaboratore' using errcode = '42501';
  end if;
  insert into public.agents (id, user_id, device_id, nome, tipo, capabilities)
  values (lower(p_agent_id), d.user_id, d.id, left(p_nome, 80), p_tipo, coalesce(p_capabilities, '{}'))
  on conflict (id) do update set device_id = excluded.device_id, nome = excluded.nome, tipo = excluded.tipo,
    capabilities = case when cardinality(excluded.capabilities) > 0 then excluded.capabilities else agents.capabilities end
  returning * into a;
  return row_to_json(a);
end $$;

create or replace function public.bridge_agent_state(p_token text, p_agent_id text, p_stato text,
  p_current_task bigint default null, p_error text default null, p_usage jsonb default null)
returns json language plpgsql security definer set search_path = public as $$
declare d public.devices; a public.agents; prima text; tipo text;
begin
  d := public._device_da_token(p_token);
  a := public._agente_del_device(d, p_agent_id);
  prima := a.stato;
  update public.agents set stato = p_stato, current_task_id = p_current_task, error = nullif(left(p_error, 500), ''),
    usage = coalesce(p_usage, usage), last_heartbeat = now(), device_id = d.id,
    last_activity = case when p_stato in ('working','waiting','needs_approval') or prima is distinct from p_stato
                         then now() else last_activity end
  where id = a.id returning * into a;
  if prima is distinct from p_stato then
    tipo := case when p_stato = 'offline' then 'agent_disconnected'
                 when prima in ('offline','unknown') then 'agent_connected'
                 when p_stato = 'error' then 'error' else 'agent_state' end;
    insert into public.activity_events (device_id, user_id, agent_id, agent_name, task_id, event_type, message, severity)
    values (d.id, d.user_id, a.id, a.nome, p_current_task, tipo,
            a.nome || ': ' || coalesce(prima, '?') || ' → ' || p_stato
              || case when coalesce(p_error, '') <> '' then ' — ' || left(p_error, 300) else '' end,
            case when p_stato = 'error' then 'error' when p_stato in ('needs_approval','waiting') then 'warning' else 'info' end);
  end if;
  return json_build_object('id', a.id, 'stato', a.stato, 'last_heartbeat', a.last_heartbeat);
end $$;

-- p_rows: [{"level","source","message","ts","task_id"}] (massimo 500 per chiamata)
create or replace function public.bridge_agent_logs(p_token text, p_agent_id text, p_rows jsonb)
returns int language plpgsql security definer set search_path = public as $$
declare d public.devices; a public.agents; n int;
begin
  d := public._device_da_token(p_token);
  a := public._agente_del_device(d, p_agent_id);
  if jsonb_array_length(coalesce(p_rows, '[]'::jsonb)) > 500 then raise exception 'Troppi log in una chiamata (max 500)'; end if;
  insert into public.agent_logs (agent_id, device_id, task_id, level, source, message, ts)
  select a.id, d.id, nullif(r->>'task_id', '')::bigint,
         case when r->>'level' in ('debug','info','warning','error') then r->>'level' else 'info' end,
         left(coalesce(r->>'source', 'bridge'), 20), left(coalesce(r->>'message', ''), 400),
         coalesce((r->>'ts')::timestamptz, now())
  from jsonb_array_elements(coalesce(p_rows, '[]'::jsonb)) r
  where coalesce(r->>'message', '') <> '';
  get diagnostics n = row_count;
  return n;
end $$;

-- Presa in carico: solo task del proprio collaboratore, non assegnati ad altri, in stato ready.
create or replace function public.bridge_claim_task(p_token text, p_agent_id text, p_task_id bigint)
returns json language plpgsql security definer set search_path = public as $$
declare d public.devices; a public.agents; t public.tasks;
begin
  d := public._device_da_token(p_token);
  a := public._agente_del_device(d, p_agent_id);
  select * into t from public.tasks where id = p_task_id for update;
  if t.id is null then raise exception 'Task inesistente'; end if;
  if t.responsabile is distinct from d.user_id then raise exception 'Task non assegnato a questo collaboratore'; end if;
  if t.assigned_agent_id is not null and t.assigned_agent_id <> a.id then raise exception 'Task assegnato a un altro agente'; end if;
  if t.stato <> 'ready' then raise exception 'Il task deve essere ready per essere preso (ora: %)', t.stato; end if;
  update public.tasks set stato = 'running', assigned_agent_id = a.id where id = t.id returning * into t;
  update public.agents set current_task_id = t.id, stato = 'working', last_activity = now() where id = a.id;
  insert into public.activity_events (device_id, user_id, agent_id, agent_name, task_id, project_id, event_type, message)
  values (d.id, d.user_id, a.id, a.nome, t.id, t.project_id, 'task_started', a.nome || ' ha preso il task #' || t.id || ': ' || t.titolo);
  return row_to_json(t);
end $$;

grant execute on function public.bridge_agent_register(text,text,text,text,text[]),
  public.bridge_agent_state(text,text,text,bigint,text,jsonb), public.bridge_agent_logs(text,text,jsonb),
  public.bridge_claim_task(text,text,bigint) to anon, authenticated;
