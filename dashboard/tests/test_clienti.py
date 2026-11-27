import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
import clienti, theme

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20
JPG = b"\xff\xd8\xff\xe0" + b"0" * 20


def test_csv_virgola_e_punto_virgola_bom_colonne_varie(tmp_path):
    (tmp_path / "a.csv").write_text("﻿azienda;categoria;zona;adattamento(1-5);prova;fonte_url\nBar Sole;bar;Cagliari;5;solo Facebook;https://x.it\n", encoding="utf-8")
    (tmp_path / "b.csv").write_text("azienda,settore,zona,adattamento,opportunita_principale\nBar Sole,bar,Cagliari,3,doppione peggiore\nStudio Rossi,studio,Quartu,4,sito\n", encoding="utf-8")
    r = clienti.leggi_leads(tmp_path)
    assert [x["azienda"] for x in r] == ["Bar Sole", "Studio Rossi"]
    assert r[0]["adattamento"] == 5 and r[0]["prova"] == "solo Facebook" and r[1]["categoria"] == "studio"   # doppione: vince il fit migliore


def test_riga_senza_azienda_e_adattamento_sporco(tmp_path):
    (tmp_path / "a.csv").write_text("azienda,adattamento\n,5\nX,abc\nY,99\n", encoding="utf-8")
    r = {x["azienda"]: x["adattamento"] for x in clienti.leggi_leads(tmp_path)}
    assert r == {"X": 0, "Y": 5}


def test_directory_mancante():
    assert clienti.leggi_leads(pathlib.Path("/non/esiste")) == []


def test_visita_stato_note_e_validazione(tmp_path):
    (tmp_path / "l").mkdir(); (tmp_path / "l" / "a.csv").write_text("azienda\nBar Sole\n")
    assert clienti.imposta_visita("bar-sole", "interessato", "ok", True, tmp_path)["ok"]
    c = clienti.clienti(tmp_path / "l", tmp_path)[0]
    assert c["stato"] == "interessato" and c["note"] == "ok" and c["consenso_foto"]
    for s, st_, n in (("../x", "no", ""), ("bar-sole", "boh", ""), ("bar-sole", "no", "a" * 2001), ("", "no", "")):
        assert not clienti.imposta_visita(s, st_, n, False, tmp_path)["ok"]


def test_foto_richiede_consenso_e_vera_immagine(tmp_path):
    assert not clienti.salva_foto("bar-sole", PNG, False, tmp_path)["ok"]                      # niente consenso
    assert not clienti.salva_foto("bar-sole", b"MZ\x90\x00 eseguibile", True, tmp_path)["ok"]  # non è un'immagine
    assert not clienti.salva_foto("bar-sole", b"<svg onload=alert(1)>", True, tmp_path)["ok"]
    assert not clienti.salva_foto("../../etc", PNG, True, tmp_path)["ok"]                       # path traversal
    assert not clienti.salva_foto("bar-sole", b"", True, tmp_path)["ok"]
    assert not clienti.salva_foto("bar-sole", PNG + b"0" * (10 * 1024 * 1024), True, tmp_path)["ok"]
    assert clienti.salva_foto("bar-sole", PNG, True, tmp_path)["ok"] and clienti.salva_foto("bar-sole", JPG, True, tmp_path)["ok"]
    f = clienti.foto("bar-sole", tmp_path)
    assert len(f) == 2 and all(x["nome"].endswith((".png", ".jpg")) for x in f)
    assert clienti.foto("../x", tmp_path) == []


def test_slug_e_url_sicuri():
    assert clienti.slug("Bar  «Sole» & C.!") == "bar-sole-c"
    assert clienti.url_sicuro("https://a.it/x") and not clienti.url_sicuro("javascript:alert(1)") and not clienti.url_sicuro("data:text/html,x")
    assert not clienti.url_sicuro("https://a.it/x\" onclick=\"y")


def test_tabella_escapa_html_degli_agenti():
    riga = {"azienda": "<script>alert(1)</script>", "categoria": "<b>x</b>", "adattamento": 4, "stato": "da visitare",
            "prova": "<img src=x onerror=alert(1)>", "fonte": "javascript:alert(1)", "slug": "x"}
    h = theme.tabella_clienti([riga])
    assert "<script>" not in h and "<img" not in h and "javascript:" not in h and "&lt;script&gt;" in h


def test_scheda_visita_solo_slug_valido(tmp_path):
    (tmp_path / "visite").mkdir(); (tmp_path / "visite" / "bar-sole.md").write_text("ciao")
    assert clienti.scheda_visita("bar-sole", tmp_path) == "ciao" and clienti.scheda_visita("../x", tmp_path) == ""
