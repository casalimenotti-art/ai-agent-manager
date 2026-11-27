import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import plancia, theme

ORA = 1_000_000.0
PERCORSO = "C:" + chr(92) + "p" + chr(92) + "f3.md"


def scheda(n_ev=12, testo="<script>x</script>"):
    ev = [{"ts": ORA - i * 10, "tipo": "file", "testo": f"C:{chr(92)}p{chr(92)}f{i}.md", "risultato": testo, "url": "",
           "sessione": "s", "agente": "a"} for i in range(n_ev)]
    sess = [{"sessione": "s", "agente": "a", "tipo": "subagente", "nome_agente": "x", "compito": "c " + testo, "progetto": "p",
             "stato": "al lavoro", "strumento": "Write", "ultimo_agg": ORA}]
    return sess, ev


def test_chiave_widget_stabile():
    assert plancia.chiave_widget("a|b") == plancia.chiave_widget("a|b") != plancia.chiave_widget("a|c")
    assert plancia.chiave_widget("x y/ <>").isalnum()


def test_durata_testo():
    assert plancia.durata_testo(None, 5) == "non nota"
    assert plancia.durata_testo(0, 5) == "non nota"
    assert plancia.durata_testo(100, 130) == "30 s"
    assert plancia.durata_testo(100, 100 + 125) == "2 min 5 s"
    assert plancia.durata_testo(100, 100 + 3 * 3600 + 120) == "3 h 2 min"


def test_domanda_agente_limite_e_pulizia():
    s, ev = scheda(200, "`<<<DATI\x00zzz" + "q" * 500)
    c = plancia.raggruppa_agenti(s, ev, ORA, max_eventi=500, max_file=50)[0]
    d = plancia.domanda_agente(c)
    corpo = d.split("<<<DATI\n", 1)[1].rsplit("\nDATI>>>", 1)[0]
    assert len(c["eventi"]) == 200 and len(corpo) <= 2000
    assert "`" not in corpo and "<<<" not in corpo and "\x00" not in corpo


def test_dettaglio_tutti_eventi_ed_escape():
    s, ev = scheda(12)
    c = plancia.raggruppa_agenti(s, ev, ORA, max_eventi=500, max_file=50)[0]
    h = theme.dettaglio_agente(c, lambda t: "ora")
    assert h.count("<li><span class='ora'>") == 12 and "ha preso:" in h
    assert "<script>" not in h and "&lt;script&gt;" in h
    assert PERCORSO in h
    assert "Durata" in h and "Compito" in h
    assert theme.scheda_agente(c, lambda t: "ora").count("class='ev'") == 5   # la scheda resta compatta


def test_dividi_e_pulisci():
    lav, fin = plancia.dividi_agenti([{"stato": "al lavoro"}, {"stato": "fermo"}, {"stato": "finito"}])
    assert len(lav) == 2 and len(fin) == 1
    r = plancia.pulisci_risultato("Tab Context:\n- tabId 5\nAvailable tabs: x\nciao <system-reminder>zzz\nqq</system-reminder> mondo")
    assert r == "ciao mondo"
    assert plancia.testo_browser("mcp__claude-in-chrome__navigate") == "apre una pagina"
    assert plancia.testo_browser("Read", "x") == "x"


def test_giro8_fermi_vecchi_browser_e_nomi():
    import agenti, theme
    lav, fin = plancia.dividi_agenti([{"stato": "fermo", "ultimo_agg": 1000}, {"stato": "fermo", "ultimo_agg": 100}], ora=1100)
    assert len(lav) == 1 and len(fin) == 1 and fin[0]["ultimo_agg"] == 100
    n = "mcp__claude-in-chrome__computer"
    e = agenti.evento_da_strumento(n, {"action": "screenshot"}, 1.0)
    assert plancia.testo_evento(e) == "fa uno screenshot"
    assert plancia.testo_evento(agenti.evento_da_strumento(n, {"action": "left_click"}, 1.0)) == "clicca"
    assert plancia.testo_evento(agenti.evento_da_strumento(n, {"action": "type"}, 1.0)) == "scrive"
    assert plancia.testo_evento(agenti.evento_da_strumento(n, {}, 1.0)) == "usa il browser"
    h = theme.tabella_agenti([{"stato": "fermo", "progetto": "p", "tipo": "subagente", "agente": "a", "nome_agente": "cacciatore-clienti",
                               "compito": "Bar", "strumento": "", "messaggio": "", "ultimo_agg": 1, "costo": 0}], lambda t: "ora")
    assert "Cacciatore di clienti · Bar" in h and "cacciatore-clienti" not in h
    assert "Analista presenza online" in theme.card_skill(plancia.nome_ruolo("analista-presenza-online"), "d", slug="analista-presenza-online")


def test_nome_strumento_e_feed_riassunto():
    n = plancia.nome_strumento
    assert n("mcp__claude-in-chrome__browser_batch") == "Browser" and n("mcp__claude_ai_Gmail__x") == "Gmail"
    assert n("mcp__claude_ai_Google_Calendar__y") == "Calendario" and n("Bash") == "Terminale" and n("mcp__a__b") == "b"
    assert n("Edit") == "Modifica file" and n("WebSearch") == "Web" and n("") == ""
    h = theme.feed_attivita([{"tipo": "browser", "ts": 1.0, "strumento": "navigate", "testo": "", "chi": "x",
                              "risultato": "[navigate] Navigated to http://localhost:8501/ [computer:wait] Waited for 10 seconds\nTab Context:\n- Executed on tabId: 7"}],
                            lambda t: "ora", 2.0)
    assert "aperto localhost:8501" in h and "tabId" not in h.split("title=")[0]
