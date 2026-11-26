import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
import fonte


def test_remota_rifiuta_http_non_locale():
    with pytest.raises(ValueError):
        fonte.FonteRemota("http://pc-collega:8000", "t")


def test_remota_richiede_token():
    with pytest.raises(ValueError):
        fonte.FonteRemota("https://pc-collega", "")


def test_remota_errore_rete_non_solleva_in_esegui():
    f = fonte.FonteRemota("http://127.0.0.1:9", "t")
    ev = list(f.esegui("x", "."))
    assert ev[-1]["type"] == "guardian_end" and ev[-1]["returncode"] == -1


def test_locale_implementa_interfaccia():
    f = fonte.FonteLocale()
    assert f.cpu_totale()["storico"] and isinstance(f.sessioni(), list) and isinstance(f.skill_elenco(), list)


def test_demo_dati_finti_e_azioni_disattivate():
    d = fonte.FonteDemo()
    assert all("ESEMPIO" in c["azienda"] for c in d.clienti())
    assert d.cpu_totale()["storico"] and d.sessioni() and d.costi(30)["giorni"] and len(d.costi(84)["giorni"]) == 84
    for r in (d.installa_skill("https://github.com/a/b"), d.installa_catalogo("seo"), d.installa_squadra(), d.imposta_azienda("x"),
              d.salva_foto("x", b"", True)):
        assert r["ok"] is False
    assert list(d.esegui("ls", "."))[-1]["returncode"] == -1                       # nessun comando eseguibile
    assert d.imposta_visita("esempio-ottica", "interessato", "ok", False)["ok"]
    assert next(c for c in d.clienti() if c["slug"] == "esempio-ottica")["stato"] == "interessato"
    import clienti as _c
    assert not _c.leggi_stati().get("esempio-ottica")                                 # niente scritto su disco


def test_crea_fonte_demo(monkeypatch):
    import config
    monkeypatch.setattr(config, "SOURCE", "demo")
    assert isinstance(fonte.crea_fonte(), fonte.FonteDemo)
