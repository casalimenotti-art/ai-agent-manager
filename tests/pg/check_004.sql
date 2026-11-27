\set ON_ERROR_STOP 1
insert into agents (id, user_id, nome, tipo) values ('amico1-codex', 'amico1', 'Codex', 'codex') on conflict do nothing;
select set_config('t.id', (select id from tasks where titolo='Claim me')::text, false);
set role anon;
do $$ declare hid bigint; r json; begin
  hid := bridge_checkpoint('tok1', 'stato', 'prossimo', current_setting('t.id')::bigint, null, null, '{}', null, null, null,
                           'test e2e', 'foto', 'non perdere', 'menotti-claude', 'amico1-codex');
  begin perform bridge_handoff_take('tok1', hid, 'amico1-codex'); raise exception 'FAIL altrui';
  exception when insufficient_privilege then null; end;
  r := bridge_handoff_take('tok2', hid, 'amico1-codex');
  assert r->>'stato' = 'preso', 'take';
  perform bridge_memory_add('tok2', 'preferenza', 'Il cliente preferisce WhatsApp', 'visita');
  begin perform bridge_memory_add('tok2', 'preferenza', 'x', ' '); raise exception 'FAIL fonte';
  exception when raise_exception then if sqlerrm like 'FAIL%' then raise; end if; end;
  assert (select count(*) from bridge_memory_search('tok1', 'whatsapp')) = 1, 'search';
  assert (select count(*) from bridge_memory_search('tok1', 'prossimo')) = 1, 'ripresa da handoff';
end $$;
reset role;
do $$ begin
  assert (select count(*) from notifications where kind='handoff_to_you' and user_id='amico1') = 1, 'notifica destinatario';
  assert (select count(*) from memory where kind='ripresa' and source like 'handoff #%') = 1, 'memoria ripresa';
  assert (select tests_pending from handoffs order by id desc limit 1) = 'test e2e', 'campi v2';
  assert (select count(*) from pg_proc where proname='bridge_checkpoint') = 1, 'una sola firma';
end $$;
select 'CHECK 004 OK';
