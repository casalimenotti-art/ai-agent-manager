\set ON_ERROR_STOP 1
-- n@x.it = amico1 (membro)
set role authenticated;
select set_config('request.jwt.claims','{"email":"n@x.it"}',false);
insert into vendite_pipeline (azienda, fase, valore_eur, fonte) values ('Bar Centrale srl', 'visita', 1200, 'leads CSV riga 4');
insert into scadenze (titolo, data, tipo, fonte) values ('F24 acconto', current_date + 5, 'fiscale', 'commercialista 20/11');
insert into costi (descrizione, importo_eur, categoria, ricorrenza, fonte) values ('Hosting siti', 1.200, 'hosting', 'mensile', 'fattura n. 12');
do $$ begin
  assert (select created_by from vendite_pipeline limit 1) = 'amico1', 'firma automatica';
  begin insert into vendite_pipeline (azienda, fonte) values ('mario.rossi@gmail.com', 'x x x'); raise exception 'FAIL email';
  exception when check_violation then null; end;
  begin insert into vendite_pipeline (azienda, prossimo_passo, fonte) values ('Bar Sole', 'chiamare 347 123 4567', 'visita'); raise exception 'FAIL telefono';
  exception when check_violation then null; end;
  begin insert into costi (descrizione, importo_eur, fonte) values ('Senza fonte', 10, ''); raise exception 'FAIL fonte';
  exception when check_violation then null; end;
  begin insert into scadenze (titolo, data, fonte, created_by) values ('a nome di altri', current_date, 'xyz', 'menotti'); raise exception 'FAIL impersonazione';
  exception when insufficient_privilege then null; end;
  update scadenze set stato = 'fatta';
  assert (select stato from scadenze limit 1) = 'fatta', 'membro aggiorna';
  delete from costi;
  assert (select count(*) from costi) = 1, 'solo admin cancella';
end $$;
reset role;
set role anon;
do $$ begin
  assert (select count(*) from vendite_pipeline) = 0, 'anon non vede';
exception when insufficient_privilege then null; end $$;
reset role;
select 'CHECK 008 OK';
