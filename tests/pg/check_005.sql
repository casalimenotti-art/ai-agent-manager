\set ON_ERROR_STOP 1
do $$ begin
  assert (select count(*) from stanze) = 3, 'tre stanze';
  assert (select responsabile from stanze where id = 'vendite') = 'amico1', 'responsabile vendite';
end $$;
insert into projects (nome, stanza_id) values ('Agenzia AI · vendite', 'vendite');
set role authenticated;
select set_config('request.jwt.claims','{"email":"n@x.it"}',false);
do $$ begin
  assert (select count(*) from stanze) = 3, 'membro legge le stanze';
  update stanze set colore = '#000000' where id = 'vendite';
  assert (select colore from stanze where id = 'vendite') = '#e76624', 'solo admin modifica';
end $$;
select set_config('request.jwt.claims','{"email":"m@x.it"}',false);
do $$ begin
  update stanze set nome = 'Vendite NEXO' where id = 'vendite';
  assert (select nome from stanze where id = 'vendite') = 'Vendite NEXO', 'admin modifica';
end $$;
select set_config('request.jwt.claims','{"email":"intruso@x.it"}',false);
do $$ begin assert (select count(*) from stanze) = 0, 'estraneo non vede'; end $$;
reset role;
do $$ begin
  begin insert into stanze (id, nome, colore) values ('x', 'X', 'rosso'); raise exception 'FAIL colore';
  exception when check_violation then null; end;
end $$;
select 'CHECK 005 OK';
