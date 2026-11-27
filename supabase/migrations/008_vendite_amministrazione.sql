-- Guardian 008 — Stanze Vendite e Amministrazione: pipeline senza dati personali, scadenze, costi con fonte.
-- Additiva e rieseguibile. Nel DB condiviso NON vanno telefoni, email o nomi di persone dei clienti:
-- la fonte unica dei clienti resta leads/2026-11-26-30-clienti.csv (AGENTS.md). Qui solo azienda o codice del lead.

-- Rifiuta email e numeri lunghi (telefoni) nei testi liberi. Anche il browser fa lo stesso controllo, ma decide il DB.
create or replace function public.senza_dati_personali(t text) returns boolean language sql immutable as $$
  select t is null or (t !~* '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}' and regexp_replace(t, '[[:space:].()/-]', '', 'g') !~ '\d{9,}')
$$;

create table if not exists public.vendite_pipeline (
  id bigserial primary key,
  azienda text not null check (length(trim(azienda)) between 2 and 120),   -- nome dell'azienda o codice del lead, mai una persona
  fase text not null default 'contatto' check (fase in ('contatto','visita','proposta','trattativa','vinto','perso')),
  valore_eur numeric(12,2) check (valore_eur is null or valore_eur >= 0),
  prossimo_passo text check (length(prossimo_passo) <= 500),
  responsabile text,                                                         -- users.id
  fonte text not null check (length(trim(fonte)) >= 3),                      -- es. "leads CSV riga 12", "visita 26/11"
  created_by text not null default public.my_user_id(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint vendite_niente_dati_personali check (public.senza_dati_personali(azienda) and public.senza_dati_personali(prossimo_passo) and public.senza_dati_personali(fonte))
);

create table if not exists public.scadenze (
  id bigserial primary key,
  titolo text not null check (length(trim(titolo)) between 2 and 200),
  data date not null,
  tipo text not null default 'altro' check (tipo in ('fiscale','contratto','pagamento','documento','altro')),
  stato text not null default 'aperta' check (stato in ('aperta','fatta','annullata')),
  importo_eur numeric(12,2) check (importo_eur is null or importo_eur >= 0),
  responsabile text,
  fonte text not null check (length(trim(fonte)) >= 3),                      -- es. "commercialista, mail 20/11"
  created_by text not null default public.my_user_id(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint scadenze_niente_dati_personali check (public.senza_dati_personali(titolo) and public.senza_dati_personali(fonte))
);

create table if not exists public.costi (
  id bigserial primary key,
  descrizione text not null check (length(trim(descrizione)) between 2 and 200),
  importo_eur numeric(12,2) not null check (importo_eur > 0),
  data date not null default current_date,
  categoria text not null default 'altro' check (categoria in ('software','abbonamenti_ai','hosting','marketing','trasporti','altro')),
  ricorrenza text not null default 'una_tantum' check (ricorrenza in ('una_tantum','mensile','annuale')),
  fonte text not null check (length(trim(fonte)) >= 3),                      -- es. "fattura n. 12", "estratto conto novembre"
  created_by text not null default public.my_user_id(),
  created_at timestamptz not null default now(),
  constraint costi_niente_dati_personali check (public.senza_dati_personali(descrizione) and public.senza_dati_personali(fonte))
);

create index if not exists idx_scadenze_aperte on public.scadenze (data) where stato = 'aperta';
create index if not exists idx_costi_data on public.costi (data desc);

drop trigger if exists vendite_updated_at on public.vendite_pipeline;
create trigger vendite_updated_at before update on public.vendite_pipeline for each row execute function public.tocca_updated_at();
drop trigger if exists scadenze_updated_at on public.scadenze;
create trigger scadenze_updated_at before update on public.scadenze for each row execute function public.tocca_updated_at();

-- Accesso: i membri attivi leggono e scrivono; chi inserisce firma con il proprio id; cancellare solo l'admin.
do $$ declare t text; begin
  foreach t in array array['vendite_pipeline','scadenze','costi'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists membri_leggono on public.%I', t);
    execute format('create policy membri_leggono on public.%I for select to authenticated using (public.is_member())', t);
    execute format('drop policy if exists membri_inseriscono on public.%I', t);
    execute format('create policy membri_inseriscono on public.%I for insert to authenticated with check (public.is_member() and created_by = public.my_user_id())', t);
    execute format('drop policy if exists membri_aggiornano on public.%I', t);
    execute format('create policy membri_aggiornano on public.%I for update to authenticated using (public.is_member()) with check (public.is_member())', t);
    execute format('drop policy if exists admin_cancella on public.%I', t);
    execute format('create policy admin_cancella on public.%I for delete to authenticated using (public.is_admin())', t);
    execute format('revoke all on public.%I from anon', t);
    execute format('grant select, insert, update, delete on public.%I to authenticated', t);
  end loop;
end $$;
grant usage on sequence public.vendite_pipeline_id_seq, public.scadenze_id_seq, public.costi_id_seq to authenticated;

do $$ begin
  alter publication supabase_realtime add table public.vendite_pipeline, public.scadenze, public.costi;
exception when others then null; end $$;
