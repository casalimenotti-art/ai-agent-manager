-- Guardian 004 — handoff v2 (destinatario, test mancanti, dipendenze, note; aperto/preso/chiuso) e memoria dal bridge.
-- Rieseguibile. Le colonne nuove di handoffs e la tabella memory esistono già (002).

-- notifica al collaboratore dell'agente destinatario
create or replace function public.handoffs_dopo_insert() returns trigger
language plpgsql security definer set search_path = public as $$
declare dest public.agents;
begin
  if new.to_agent_id is not null then
    select * into dest from public.agents where id = new.to_agent_id;
    if dest.id is not null then
      perform public.notifica(dest.user_id, 'handoff_to_you', 'Handoff per ' || dest.nome || ': ' || new.next_step,
                              'handoffs', new.id::text);
    end if;
  end if;
  return new;
end $$;
drop trigger if exists handoffs_notifica on public.handoffs;
create trigger handoffs_notifica after insert on public.handoffs for each row execute function public.handoffs_dopo_insert();

alter table public.handoffs drop constraint if exists handoffs_to_agent_fk;
alter table public.handoffs add constraint handoffs_to_agent_fk
  foreign key (to_agent_id) references public.agents(id) on delete set null;

-- bridge_checkpoint v2: sostituisce la firma di 001 (stessi primi parametri, nuovi facoltativi)
drop function if exists public.bridge_checkpoint(text,text,text,bigint,text,text,text[],text,text,text);
create or replace function public.bridge_checkpoint(p_token text, p_summary text, p_next_step text,
  p_task_id bigint default null, p_agent_name text default null, p_completed_steps text default null,
  p_files_changed text[] default '{}', p_decisions text default null, p_errors text default null,
  p_tests text default null, p_tests_pending text default null, p_dependencies text default null,
  p_important_notes text default null, p_from_agent_id text default null, p_to_agent_id text default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare d public.devices; hid bigint; agente text; t public.tasks; dest public.agents; testo text;
begin
  d := public._device_da_token(p_token);
  if p_from_agent_id is not null then perform public._agente_del_device(d, p_from_agent_id); end if;
  if p_to_agent_id is not null then
    select * into dest from public.agents where id = lower(p_to_agent_id);
    if dest.id is null then raise exception 'Agente destinatario inesistente: %', p_to_agent_id; end if;
  end if;
  agente := coalesce(nullif(p_agent_name,''), d.agent_name, d.nome);
  insert into public.handoffs (task_id, device_id, agent_name, summary, completed_steps, files_changed, decisions, errors,
    tests, next_step, tests_pending, dependencies, important_notes, from_agent_id, to_agent_id, stato)
  values (p_task_id, d.id, agente, p_summary, p_completed_steps, coalesce(p_files_changed,'{}'), p_decisions, p_errors,
    p_tests, p_next_step, p_tests_pending, p_dependencies, p_important_notes, lower(p_from_agent_id), dest.id, 'aperto')
  returning id into hid;
  if p_task_id is not null then
    update public.tasks set next_step = p_next_step where id = p_task_id returning * into t;
    testo := 'Prossimo passo: ' || p_next_step || E'\nStato: ' || left(p_summary, 1200)
      || case when coalesce(p_tests_pending,'') <> '' then E'\nTest ancora necessari: ' || left(p_tests_pending, 500) else '' end
      || case when coalesce(p_important_notes,'') <> '' then E'\nDa non perdere: ' || left(p_important_notes, 800) else '' end;
    insert into public.memory (project_id, task_id, kind, content, source, created_by)
    values (t.project_id, p_task_id, 'ripresa', testo, 'handoff #' || hid, d.user_id);
  end if;
  update public.devices set last_checkpoint = now() where id = d.id;
  insert into public.activity_events (task_id, device_id, user_id, agent_id, agent_name, project_id, event_type, message, files)
  values (p_task_id, d.id, d.user_id, lower(p_from_agent_id), agente, t.project_id,
          case when dest.id is null then 'checkpoint' else 'handoff' end,
          'Handoff salvato' || case when dest.id is null then '' else ' → ' || dest.nome end
            || '. Prossimo passo: ' || left(p_next_step, 500), coalesce(p_files_changed,'{}'));
  return hid;
end $$;

create or replace function public.bridge_handoff_take(p_token text, p_handoff_id bigint, p_agent_id text)
returns json language plpgsql security definer set search_path = public as $$
declare d public.devices; a public.agents; h public.handoffs;
begin
  d := public._device_da_token(p_token);
  a := public._agente_del_device(d, p_agent_id);
  update public.handoffs set stato = 'preso', to_agent_id = a.id where id = p_handoff_id and stato = 'aperto'
  returning * into h;
  if h.id is null then raise exception 'Handoff inesistente o già preso'; end if;
  insert into public.activity_events (task_id, device_id, user_id, agent_id, agent_name, event_type, message)
  values (h.task_id, d.id, d.user_id, a.id, a.nome, 'handoff_taken', 'Handoff #' || h.id || ' preso da ' || a.nome);
  return row_to_json(h);
end $$;

create or replace function public.bridge_memory_add(p_token text, p_kind text, p_content text, p_source text,
  p_project_id bigint default null, p_task_id bigint default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare d public.devices; mid bigint;
begin
  d := public._device_da_token(p_token);
  if coalesce(trim(p_source), '') = '' then raise exception 'La fonte è obbligatoria'; end if;
  insert into public.memory (project_id, task_id, kind, content, source, created_by)
  values (p_project_id, p_task_id, p_kind, left(p_content, 4000), left(p_source, 300), d.user_id) returning id into mid;
  return mid;
end $$;

create or replace function public.bridge_memory_search(p_token text, p_q text default null,
  p_project_id bigint default null, p_task_id bigint default null)
returns setof public.memory language plpgsql stable security definer set search_path = public as $$
begin
  perform public._device_da_token(p_token);
  return query select * from public.memory m
    where m.superseded_by is null
      and (p_project_id is null or m.project_id = p_project_id) and (p_task_id is null or m.task_id = p_task_id)
      and (coalesce(p_q, '') = '' or m.ricerca @@ plainto_tsquery('italian', p_q) or m.content ilike '%' || p_q || '%')
    order by m.created_at desc limit 50;
end $$;

grant execute on function
  public.bridge_checkpoint(text,text,text,bigint,text,text,text[],text,text,text,text,text,text,text,text),
  public.bridge_handoff_take(text,bigint,text), public.bridge_memory_add(text,text,text,text,bigint,bigint),
  public.bridge_memory_search(text,text,bigint,bigint) to anon, authenticated;
