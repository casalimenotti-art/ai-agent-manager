#!/usr/bin/env python3
"""Finto claude per provare la voce: risposta lunga in più frasi, con codice e link, a pezzetti."""
import json, sys, time
sys.stdin.read()
out = lambda o: print(json.dumps(o), flush=True)
out({"type": "system", "subtype": "init", "session_id": "voce-1"})
pezzi = ["Ho trovato tre clienti a Cagliari. ", "Il primo è un ristorante **senza sito**, vedi https://example.com/a per la prova. ",
         "```bash\nrm -rf cose\n```\n", "Il secondo è un B&B con le prenotazioni solo al telefono. ", "Ti consiglio di partire da quello"]
for p in pezzi:
    out({"type": "stream_event", "session_id": "voce-1", "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": p}}})
    time.sleep(0.4)
out({"type": "result", "session_id": "voce-1", "result": "x", "total_cost_usd": 0.01, "is_error": False})
