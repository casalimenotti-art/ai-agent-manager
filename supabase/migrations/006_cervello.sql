-- Guardian 006 — Il "cervello" di Guardian sul PC del titolare (Claude Code in sola risposta) raggiungibile da ogni dispositivo.
-- L'HQ scrive una richiesta; il bridge del PC dell'admin la prende, chiede a `claude -p` (niente strumenti di scrittura)
-- e scrive la risposta a frasi; Realtime la porta all'HQ. Funziona solo quando quel PC è acceso. Rieseguibile.

create table if not exists public.guardian_cervello (
  id int primary key default 1 check (id = 1),     -- una sola riga: lo stato del cervello
  device_id bigint references public.devices(id) on delete set null,
  modello text,
  ultimo_battito timestamptz
);

create table if not exists public.guardian_richieste (
  id bigint generated always as identity primary key,
  user_id text not null references public.users(id),
  testo text not null check (char_length(testo) between 1 and 2000),
  contesto jsonb not null default '{}',           -- contesto minimo (stanza/pannello aperto, numeri), mai dati personali
  stato text not null default 'nuova' check (stato in ('nuova', 'presa', 'completata', 'errore')),
  device_id bigint references public.devices(id) on delete set null,
  created_at timestamptz not null default now(),
  presa_at timestamptz
);
create index if not exists idx_richieste_nuove on public.guardian_richieste (created_at) where stato = 'nuova';

create table if not exists public.guardian_risposte (
  id bigint generated always as identity primary key,
  richiesta_id bigint not null references public.guardian_richieste(id) on delete cascade,
  seq int not null,
  testo text not null default '',
  fine boolean not null default false,
  created_at timestamptz not null default now(),
  unique (richiesta_id, seq)
);

alter table public.guardian_cervello enable row level security;
alter table public.guardian_richieste enable row level security;
alter table public.guardian_risposte enable row level security;
drop policy if exists membri_leggono on public.guardian_cervello;
create policy membri_leggono on public.guardian_cervello for select to authenticated using (public.is_member());
drop policy if exists proprie_scrive on public.guardian_richieste;
create policy proprie_scrive on public.guardian_richieste for insert to authenticated with check (user_id = public.my_user_id());
drop policy if exists proprie_legge on public.guardian_richieste;
create policy proprie_legge on public.guardian_richieste for select to authenticated using (user_id = public.my_user_id());
drop policy if exists proprie_risposte on public.guardian_risposte;
create policy proprie_risposte on public.guardian_risposte for select to authenticated
  using (exists (select 1 from public.guardian_richieste r where r.id = richiesta_id and r.user_id = public.my_user_id()));
revoke all on public.guardian_cervello, public.guardian_richieste, public.guardian_risposte from anon;
revoke update, delete on public.guardian_richieste, public.guardian_risposte from authenticated;
revoke insert, update, delete on public.guardian_risposte, public.guardian_cervello from authenticated;

-- solo il PC di un admin può fare da cervello
create or replace function public._device_cervello(p_token text) returns public.devices
language plpgsql stable security definer set search_path = public as $$
declare d public.devices;
begin
  d := public._device_da_token(p_token);
  if not exists (select 1 from public.users where id = d.user_id and accesso = 'admin' and stato = 'attivo') then
    raise exception 'Solo il PC di un admin può fare da cervello' using errcode = '42501';
  end if;
  return d;
end $$;
revoke all on function public._device_cervello(text) from public, anon, authenticated;

create or replace function public.bridge_cervello_battito(p_token text, p_modello text default null)
returns void language plpgsql security definer set search_path = public as $$
declare d public.devices;
begin
  d := public._device_cervello(p_token);
  insert into public.guardian_cervello (id, device_id, modello, ultimo_battito) values (1, d.id, left(p_modello, 80), now())
  on conflict (id) do update set device_id = excluded.device_id, modello = coalesce(excluded.modello, guardian_cervello.modello),
    ultimo_battito = now();
end $$;

create or replace function public.bridge_prendi_richiesta(p_token text)
returns json language plpgsql security definer set search_path = public as $$
declare d public.devices; r public.guardian_richieste; nome text;
begin
  d := public._device_cervello(p_token);
  select * into r from public.guardian_richieste where stato = 'nuova' and created_at > now() - interval '5 minutes'
    order by created_at limit 1 for update skip locked;
  if r.id is null then return null; end if;
  update public.guardian_richieste set stato = 'presa', presa_at = now(), device_id = d.id where id = r.id;
  select u.nome into nome from public.users u where u.id = r.user_id;
  return json_build_object('id', r.id, 'testo', r.testo, 'contesto', r.contesto, 'utente', coalesce(nome, r.user_id));
end $$;

create or replace function public.bridge_rispondi(p_token text, p_richiesta_id bigint, p_seq int, p_testo text, p_fine boolean default false,
  p_errore boolean default false)
returns void language plpgsql security definer set search_path = public as $$
declare d public.devices;
begin
  d := public._device_cervello(p_token);
  insert into public.guardian_risposte (richiesta_id, seq, testo, fine) values (p_richiesta_id, p_seq, left(coalesce(p_testo, ''), 2000), p_fine)
  on conflict (richiesta_id, seq) do nothing;
  if p_fine then
    update public.guardian_richieste set stato = case when p_errore then 'errore' else 'completata' end where id = p_richiesta_id;
  end if;
end $$;

-- pulizia: richieste e risposte più vecchie di 7 giorni (da pianificare o eseguire a mano)
create or replace function public.pulisci_cervello(p_giorni int default 7) returns int
language sql security definer set search_path = public as $$
  with x as (delete from public.guardian_richieste where created_at < now() - make_interval(days => p_giorni) returning 1) select count(*)::int from x;
$$;
revoke all on function public.pulisci_cervello(int) from public, anon, authenticated;

grant execute on function public.bridge_cervello_battito(text, text), public.bridge_prendi_richiesta(text),
  public.bridge_rispondi(text, bigint, int, text, boolean, boolean) to anon, authenticated;

do $$ begin
  alter publication supabase_realtime add table public.guardian_risposte, public.guardian_cervello;
exception when others then null; end $$;
