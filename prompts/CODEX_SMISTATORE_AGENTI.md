# Guardian HQ — Smistatore automatico degli agenti (prompt per Codex)

Lingua: italiano. Il titolare è Menotti ("fratello"). Lavora a blocchi piccoli, verifica ogni blocco, fai commit + push a ogni blocco verificato.

## Contesto (da portare avanti)
- Repo: casalimenotti-art/ai-agent-manager, branch `claude/gallant-sagan-fwncjr`. Leggi prima: AGENTS.md, guardian-web/DESIGN-GUARDIAN.md, guardian-web/ROADMAP.md, bridge/guardian_bridge.py, bridge/cervello.py.
- Stack: guardian-web/ (React + Supabase, online su Cloudflare Pages guardian-nexo.pages.dev), supabase/migrations/001…008, bridge Python sul PC di ogni socio (`python bridge/guardian_bridge.py run`), test in tests/ (`python -m pytest -q tests`).
- Esiste già: tabelle tasks, approvals, notifications, agents, devices, handoffs; RPC `bridge_claim_task` + comando `claim`; collector claude_code.py e codex.py; hook di stato live; cervello (Claude, riserva Codex in sola lettura solo per l'admin).
- Soci (registro/persone.json): menotti = Claude Code (PC-Menotti, ha anche Codex gratis), amico1 = Codex, amico2 = Codex. I tre soci hanno dato per iscritto il consenso a usare i PC/account l'uno dell'altro tramite Guardian. Lancio dei task: SENZA approvazione per i tre soci.

## Obiettivo
Dalla dashboard web uno dei tre soci scrive un lavoro (es. "realizza una demo di sito per l'azienda X"). Guardian, in automatico:
1. Spezza il lavoro in parti (es. ricerca, design, codice, controllo) solo se serve.
2. Per ogni parte sceglie DOVE (Claude Code di Menotti, Codex di amico1, Codex di amico2, Codex gratis di Menotti) e CON QUALE POTENZA (modello ed effort), bilanciando l'utilizzo: va a chi ha l'utilizzo percentuale più basso tra i PC online e capaci, a parità di qualità richiesta.
3. Sceglie le skill pertinenti (solo quelle) e le passa all'agente.
4. Lancia l'agente sul PC scelto senza approvazione; stato e rapporto finale compaiono nella dashboard.

## Blocchi (in ordine; ognuno con test e verifica prima del successivo)
1. **Utilizzo per PC**: il bridge legge l'utilizzo di ogni motore e lo manda col battito (nuova colonna/tabella in una migrazione 009).
   - Claude: `~/.claude/guardian/usage.json` (five_hour.pct, seven_day.pct, resets_at).
   - Codex: VERIFICATO sul PC di Menotti (28/11): l'ultimo file `~/.codex/sessions/AAAA/MM/GG/rollout-*.jsonl` contiene `"rate_limits":{"primary":{"used_percent":31.0,"window_minutes":43200,"resets_at":…},"plan_type":"free",…}` → usa l'ultimo `rate_limits` del file più recente (finestra in minuti: 43200 = 30 giorni sul piano free; i piani a pagamento possono avere primary/secondary diversi). Le esecuzioni `--ephemeral` potrebbero non scrivere il file: verificalo.
   - ATTENZIONE: il Codex free di Menotti era già al 31% del mese dopo ~5 domande: va usato per ultimo e per lavori piccoli.
2. **Smistatore** (funzione pura Python in bridge/ + stessa logica nell'RPC o nel web, con test): input = parti del lavoro + stato dei PC; output = per parte {pc, motore, modello, effort, skill}. Regole: escludi PC offline (battito > 2 min) e motori oltre il 95% (5 ore) o 98% (settimana); tra i rimanenti scegli il più scarico; potenza per tipo di parte: lavori semplici/ripetitivi → modello leggero ed effort basso; codice di sito/software e design → modello forte; ricerca → medio. Verifica i nomi dei modelli con `claude --help` / `codex exec --help` e la config dei PC, NON scriverli a memoria.
3. **Esecutore sul PC** (`guardian_bridge.py run`): prende i task assegnati al suo PC (bridge_claim_task) e lancia:
   - Claude: `claude -p --permission-mode acceptEdits --model <m>` nella cartella del progetto (es. `~/guardian-lavori/<task-id>/`), compito via stdin.
   - Codex: `codex exec -s workspace-write -m <m> -C <cartella>` con compito via stdin.
   - MAI `--dangerously-skip-permissions`, `bypassPermissions`, `danger-full-access`, `--dangerously-bypass-approvals-and-sandbox`.
   - Timeout, una sola esecuzione per task (niente doppi lanci), output e rapporto salvati nel task, git init nella cartella per poter tornare indietro.
4. **Comandi sul PC con notifica**: le modifiche ai file nella cartella del progetto sono automatiche. Ogni comando di shell fuori da una lista sicura (es. `npm install`, `npm run build`, `git` locale, `python -m pytest`) crea un'approvazione + notifica al proprietario del PC con: comando esatto, cartella, chi l'ha chiesto, e un GIUDIZIO DI SICUREZZA (sicuro / dubbio / pericoloso + motivo in una riga) dato dal motore più scarico in sola lettura. Il comando parte solo dopo il clic del proprietario. Per Claude usa gli hook PreToolUse; per Codex usa le approvazioni della CLI. Verifica come funzionano nella versione installata.
5. **Skill automatiche**: catalogo delle skill installate (nome + descrizione da ogni SKILL.md in `~/.claude/skills`, plugin, `~/.codex`); per ogni parte scegli al massimo 3 skill pertinenti (corrispondenza su descrizione + tipo di parte, con test su casi: "sito per ristorante" → design/frontend sì, remotion/xlsx no) e scrivile nel compito ("Usa le skill: …"). Per i siti demo: obbligatoria web-design-guidelines + frontend-design; niente fatti inventati su orari/prezzi del cliente.
6. **Dashboard**: modulo "Nuovo lavoro" (testo + progetto), vista dei piani di smistamento (chi fa cosa, perché, con quale modello), stato live, pulsante Ferma, centro approvazioni con il giudizio di sicurezza. Segui DESIGN-GUARDIAN.md e le linee guida web (a11y, mobile).

## Vincoli
- Fai solo quanto richiesto: niente dipendenze nuove senza motivo scritto nel commit.
- Sicurezza sempre: solo i tre soci autenticati possono creare lavori (RLS), ogni lancio registrato con chi l'ha chiesto, niente segreti nei log o nel registro, nessun invio esterno (email, messaggi, pubblicazioni, pagamenti) senza approvazione.
- Ogni migrazione nuova: GRANT ad authenticated + test in tests/pg come per le precedenti.
- Fermati e chiedi a Menotti prima di: cancellare file, cambiare tabelle esistenti in modo non additivo, toccare le impostazioni di Claude Code/Codex dei PC.

## Fatto quando
- Da guardian-nexo.pages.dev, "crea una pagina HTML di prova con scritto ciao" viene assegnato in automatico al motore più scarico, gira sul PC giusto senza clic, e il risultato compare nella dashboard.
- Un comando non in lista sicura produce una notifica con giudizio di sicurezza e parte solo dopo il clic.
- `python -m pytest -q tests` tutto verde.
- A fine di ogni blocco: `python registro/scrivi.py --chi <tuo-id> --agente codex "…" --file … --esito fatto`, commit, push su `claude/gallant-sagan-fwncjr`.

## Rapporto (max 8 righe a blocco)
File cambiati, prove (test, screenshot o output), cosa resta, eventuali dati non verificati.
