# Collegare un PC a Guardian HQ

Tre passi. Serve un account amministratore in Guardian HQ e Python sul PC da collegare.

## 1. Registra il PC

1. In Guardian HQ apri il pannello **Dispositivi** (visibile solo agli amministratori).
2. In **Registra PC** scrivi il nome del PC (es. `PC-Menotti`), scegli la persona e premi **Registra PC**.
3. Compare il codice del dispositivo. Premi **Copia**: **non verrà più mostrato**. Nel database resta solo il suo hash.
   Se lo perdi, revoca il PC dallo stesso pannello e registralo di nuovo.

## 2. Compila `bridge/.env`

1. Nella cartella `bridge/` copia `.env.example` in `.env` (il file `.env` è escluso da git: non committarlo mai).
2. Apri `bridge/.env` e imposta:
   - `GUARDIAN_SUPABASE_URL`: indirizzo del progetto Supabase (te lo dà l'amministratore).
   - `GUARDIAN_SUPABASE_ANON_KEY`: la chiave pubblica "anon" del progetto.
   - `GUARDIAN_DEVICE_TOKEN`: il codice copiato al passo 1.
3. Gli altri campi (`GUARDIAN_AGENT`, ecc.) sono descritti nei commenti di `.env.example`.

## 3. Avvia il bridge

Doppio clic su `bridge/avvia-bridge.bat`. Lascia la finestra aperta: dopo pochi istanti il PC compare nel pannello **Dispositivi** come **online**
(online = ultimo segnale ricevuto meno di 5 minuti fa).

## Per revocare un PC

Pannello **Dispositivi**, tasto **Revoca** accanto al PC: il bridge di quel PC smette di funzionare.
