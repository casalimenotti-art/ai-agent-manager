-- Guardian 005 — Le tre stanze dell'HQ (Sviluppo & Siti, Vendite, Amministrazione) come DATI, non codice.
-- Una stanza raggruppa aziende (projects) e ha un responsabile (users.id) i cui agenti lavorano lì.
-- Additiva e rieseguibile. Nessun dato personale.

create table if not exists public.stanze (
  id text primary key,                         -- es. 'vendite'
  nome text not null,
  descrizione text,
  colore text not null default '#338ced' check (colore ~ '^#[0-9a-fA-F]{6}$'),
  responsabile text,                           -- users.id (senza FK: la stanza può esistere prima dell'utente)
  ordine int not null default 0,
  attiva boolean not null default true,
  created_at timestamptz not null default now()
);

alter table public.projects add column if not exists stanza_id text references public.stanze(id) on delete set null;
create index if not exists idx_projects_stanza on public.projects (stanza_id);

-- Le tre stanze iniziali (struttura dell'azienda, modificabile dall'admin).
insert into public.stanze (id, nome, descrizione, colore, responsabile, ordine) values
  ('sviluppo', 'Sviluppo & Siti', 'Siti, software, test e la dashboard', '#338ced', 'menotti', 1),
  ('vendite', 'Vendite', 'Solo vendite: lead, visite, bozze, preventivi, esiti', '#e76624', 'amico1', 2),
  ('amministrazione', 'Amministrazione', 'SRL, scadenze, documenti, costi, fornitori', '#9887ef', 'amico2', 3)
on conflict (id) do nothing;

alter table public.stanze enable row level security;
drop policy if exists membri_leggono on public.stanze;
create policy membri_leggono on public.stanze for select to authenticated using (public.is_member());
drop policy if exists admin_scrive on public.stanze;
create policy admin_scrive on public.stanze for all to authenticated using (public.is_admin()) with check (public.is_admin());
revoke all on public.stanze from anon;

do $$ begin
  alter publication supabase_realtime add table public.stanze, public.projects;
exception when others then null; end $$;
