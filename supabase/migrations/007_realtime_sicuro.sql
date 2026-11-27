-- Guardian 007 — Realtime più sicuro (rieseguibile, non cancella dati).
-- I messaggi Realtime "postgres_changes" portano la riga intera: per `devices` includerebbero `token_hash`,
-- che i browser non devono mai vedere (in 001 la colonna è esclusa dalle select). Quindi `devices` esce dalla
-- pubblicazione: lo stato dei PC arriva con il ricaricamento completo (subito dopo ogni cambio degli agenti, o polling).
do $$ begin
  if exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'devices') then
    alter publication supabase_realtime drop table public.devices;
  end if;
exception when undefined_object then null; end $$;
