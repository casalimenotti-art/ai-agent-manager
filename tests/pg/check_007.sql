\set ON_ERROR_STOP 1
do $$ begin
  assert not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'devices'), 'devices fuori dal realtime';
  assert exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'tasks'), 'tasks resta nel realtime';
end $$;
select 'CHECK 007 OK';
