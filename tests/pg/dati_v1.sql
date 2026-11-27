-- Dati in formato 001 (vecchi stati, titoli duplicati) per provare la conversione di 002.
insert into users (id,nome,email) values ('menotti','Menotti','m@x.it'),('amico1','Niko','n@x.it'),('amico2','Fra','f@x.it');
insert into devices (user_id,nome,agent_name,token_hash) values
  ('menotti','PC','Claude Code', encode(sha256(convert_to('tok1','UTF8')),'hex'));
insert into tasks (titolo,responsabile,stato) values ('Sito','menotti','in attesa'),('Sito','amico1','in corso'),
  ('Vecchio','menotti','completato'),('Bloccato','amico1','bloccato');
