\set ON_ERROR_STOP 1
-- tok1 = PC di menotti (admin), tok2 = PC di amico1 (membro)
set role authenticated;
select set_config('request.jwt.claims','{"email":"n@x.it"}',false);
insert into guardian_richieste (user_id, testo, contesto) values ('amico1', 'Come va la stanza vendite?', '{"stanza":"vendite"}');
do $$ begin
  begin insert into guardian_richieste (user_id, testo) values ('menotti', 'a nome di altri'); raise exception 'FAIL impersonazione';
  exception when insufficient_privilege then null; end;
  assert (select count(*) from guardian_richieste) = 1, 'vede solo le proprie';
end $$;
reset role;
set role anon;
do $$ declare r json; begin
  begin perform bridge_prendi_richiesta('tok2'); raise exception 'FAIL non admin';
  exception when insufficient_privilege then null; end;
  perform bridge_cervello_battito('tok1', 'claude-code');
  r := bridge_prendi_richiesta('tok1');
  assert r->>'testo' = 'Come va la stanza vendite?' and r->'contesto'->>'stanza' = 'vendite', 'presa';
  assert bridge_prendi_richiesta('tok1') is null, 'non la riprende due volte';
  perform bridge_rispondi('tok1', (r->>'id')::bigint, 0, 'Vendite: due task attivi.');
  perform bridge_rispondi('tok1', (r->>'id')::bigint, 1, '', true);
end $$;
reset role;
set role authenticated;
select set_config('request.jwt.claims','{"email":"n@x.it"}',false);
do $$ begin
  assert (select string_agg(testo, '|' order by seq) from guardian_risposte) = 'Vendite: due task attivi.|', 'risposte visibili al richiedente';
  assert (select stato from guardian_richieste) = 'completata', 'completata';
  assert (select modello from guardian_cervello) = 'claude-code', 'battito visibile';
end $$;
select set_config('request.jwt.claims','{"email":"m@x.it"}',false);
do $$ begin assert (select count(*) from guardian_risposte) = 0, 'altri non vedono le risposte'; end $$;
reset role;
select 'CHECK 006 OK';
