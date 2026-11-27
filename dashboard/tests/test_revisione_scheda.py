import plancia


def test_accorcia_a_fine_parola():
    t = "la pagina si carica senza errori e tutto funziona bene"
    r = plancia.accorcia(t, 30)
    assert r.endswith("…") and len(r) <= 31
    assert t.startswith(r[:-1]) and t[len(r) - 1] == " "
    assert plancia.accorcia("corto", 30) == "corto"


def test_riassumi_risultato_browser():
    g = ("[navigate] Navigated to http://localhost:8501/ [computer:wait] Waited for 9 seconds "
         "[computer:screenshot] Successfully captured screenshot (922x383, jpeg) - ID:")
    assert plancia.riassumi_risultato(g) == "aperto localhost:8501 · atteso 9 s · screenshot"


def test_riassumi_risultato_libero_tronca():
    r = plancia.riassumi_risultato("parola " * 40)
    assert len(r) <= 81 and r.endswith("…")


def test_riassumi_risultato_nasconde_metadati_interni():
    for g in ("Async agent launched successfully. (This tool result is internal metadata", "agentId: abc123 done"):
        assert plancia.riassumi_risultato(g) == "avviato in background"


def test_testo_semplice():
    ts = plancia.testo_semplice
    assert ts("Fratello, va **tutto** bene") == "Fratello, va tutto bene"
    assert ts("Ok:\n- **Pannello:** mostra 5 ore\n1. due\n2. tre") == "Ok: Pannello: mostra 5 ore due tre"
    assert ts("vedi [la guida](http://x.it/a) ora") == "vedi la guida ora"
    assert ts("apri `app.py` e *poi* #x") == "apri app.py e poi #x"
    assert ts("# Titolo\n| a | b |\n|---|---|\n| 1 | 2 |") == "Titolo a · b 1 · 2"
    assert plancia.testo_evento({"tipo": "dice", "testo": "**ciao**\n\n- uno"}) == "ciao uno"
