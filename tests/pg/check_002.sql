\set ON_ERROR_STOP 1
-- conversione stati e titoli duplicati
do $$ begin
  assert (select string_agg(stato, ',' order by id) from tasks) = 'ready,running,completed,blocked', 'conversione stati';
  assert (select titolo from tasks where id=2) = 'Sito (#2)', 'titolo duplicato rinominato';
end $$;
-- vincoli: duplicato aperto, dipendenze, un running per agente
insert into agents (id,user_id,nome,tipo) values ('menotti-claude','menotti','Claude Code','claude-code');
do $$ begin
  begin insert into tasks (titolo) values ('sito'); raise exception 'FAIL dup';
  exception when unique_violation then null; end;
  insert into tasks (titolo, stato) values ('Vecchio', 'backlog');  -- il completato non conta
  begin insert into tasks (titolo, stato, depends_on) values ('Dip', 'ready', array[4]::bigint[]); raise exception 'FAIL dip';
  exception when raise_exception then if sqlerrm like 'FAIL%' then raise; end if; end;
  insert into tasks (titolo, stato, depends_on) values ('Dip2', 'planned', array[3]::bigint[]);
  update tasks set stato='ready' where titolo='Dip2';           -- dipende da completato: ok
  update tasks set assigned_agent_id='menotti-claude', stato='running' where id=1;
  begin update tasks set assigned_agent_id='menotti-claude', stato='running' where titolo='Dip2'; raise exception 'FAIL run';
  exception when unique_violation then null; end;
end $$;
-- approvazioni -> needs_approval -> ready / blocked + notifiche
insert into approvals (task_id, action, action_type, requested_by) values (4, 'Inviare email', 'email', 'amico1');
do $$ begin
  assert (select stato from tasks where id=4) = 'needs_approval', 'needs_approval';
  assert (select count(*) from notifications where kind='approval_requested') = 3, 'notifica a tutti';
end $$;
update approvals set status='approvata', decided_by='menotti' where task_id=4;
do $$ begin
  assert (select stato from tasks where id=4) = 'ready', 'approvata -> ready';
  assert (select count(*) from notifications where kind='approval_decided' and user_id='amico1') = 1, 'notifica richiedente';
end $$;
update tasks set stato='failed' where id=1;
update agents set stato='error', error='crash' where id='menotti-claude';
do $$ begin
  assert (select count(*) from notifications where kind='task_failed' and user_id='menotti') = 1, 'notifica task failed';
  assert (select count(*) from notifications where kind='agent_error' and user_id='menotti') = 1, 'notifica agente';
end $$;
-- RLS: membro, admin, estraneo, notifiche private, revoca dispositivi
update users set accesso='admin' where id='menotti';
set role authenticated;
select set_config('request.jwt.claims','{"email":"n@x.it"}',false);
do $$ begin
  assert (select count(*) from notifications) = (select count(*) from notifications where user_id='amico1'), 'solo proprie notifiche';
  assert (select count(*) from projects) = 0;
  insert into projects (nome) values ('Nexo');
  insert into memory (kind, content, source) values ('decisione', 'Usiamo Supabase come backend', 'GUARDIAN_DECISIONS.md');
  assert (select count(*) from memory where ricerca @@ plainto_tsquery('italian','supabase')) = 1, 'ricerca memoria';
  update devices set nome='hack' where user_id='menotti';
  assert (select count(*) from devices where nome='hack') = 0, 'non può modificare PC altrui';
  update users set accesso='admin' where id='amico1';
  assert (select accesso from users where id='amico1') = 'member', 'non admin non cambia utenti';
end $$;
select set_config('request.jwt.claims','{"email":"m@x.it"}',false);
do $$ begin
  update devices set nome='PC-Menotti' where user_id='menotti';
  assert (select nome from devices where user_id='menotti') = 'PC-Menotti', 'proprietario modifica';
end $$;
select set_config('request.jwt.claims','{"email":"intruso@x.it"}',false);
do $$ begin
  assert (select count(*) from tasks) = 0 and (select count(*) from memory) = 0 and (select count(*) from notifications) = 0, 'estraneo';
end $$;
reset role;
set role anon;
do $$ begin
  assert (select count(*) from bridge_pull_tasks('tok1')) = 0, 'pull dopo failed';
  begin perform count(*) from agents; raise exception 'FAIL anon';
  exception when insufficient_privilege then null; end;
end $$;
reset role;
select 'CHECK 002 OK';
