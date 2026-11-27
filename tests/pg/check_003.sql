\set ON_ERROR_STOP 1
insert into devices (user_id,nome,token_hash) values ('amico1','PC-N', encode(sha256(convert_to('tok2','UTF8')),'hex'));
set role anon;
do $$ declare r json; begin
  r := bridge_agent_register('tok1', 'Menotti-Claude', 'Claude Code', 'claude-code', array['python']);
  assert r->>'id' = 'menotti-claude', 'register';
  begin perform bridge_agent_state('tok2', 'menotti-claude', 'working'); raise exception 'FAIL altrui';
  exception when insufficient_privilege then null; end;
  r := bridge_agent_state('tok1', 'menotti-claude', 'working', null, null, '{"five_hour":{"pct":12}}');
  assert r->>'stato' = 'working', 'state';
  assert bridge_agent_logs('tok1', 'menotti-claude', '[{"message":"Strumento: Bash","source":"hook"},{"message":""}]') = 1, 'logs';
end $$;
reset role;
insert into tasks (titolo, responsabile, stato) values ('Claim me', 'menotti', 'ready'), ('Di Niko', 'amico1', 'ready');
select set_config('t.mio', (select id from tasks where titolo='Claim me')::text, false),
       set_config('t.altrui', (select id from tasks where titolo='Di Niko')::text, false);
set role anon;
do $$ declare r json; begin
  r := bridge_claim_task('tok1', 'menotti-claude', current_setting('t.mio')::bigint);
  assert r->>'stato' = 'running', 'claim';
  begin perform bridge_claim_task('tok1', 'menotti-claude', current_setting('t.altrui')::bigint); raise exception 'FAIL claim altrui';
  exception when raise_exception then if sqlerrm like 'FAIL%' then raise; end if; end;
end $$;
reset role;
do $$ begin
  assert (select count(*) from activity_events where event_type in ('agent_state','task_started') and agent_id='menotti-claude') >= 2, 'eventi';
  assert (select usage->'five_hour'->>'pct' from agents where id='menotti-claude') = '12', 'usage';
end $$;
select 'CHECK 003 OK';
