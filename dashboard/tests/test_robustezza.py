"""Stati vuoti e dati mancanti: nessuna eccezione, messaggi chiari. Solo file temporanei."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import clienti
import config
import fonte
import plancia
import storico
import theme

ORA = 1_800_000_000.0


def titoli(d):
    return {b["titolo"]: b for b in d["barre"]}


def test_five_hour_null_file_recente_appena_azzerato():
    d = plancia.descrivi_usage({"five_hour": None, "seven_day": {"pct": 30, "resets_at": ORA + 86400}, "ts": ORA - 30}, ORA)
    b = titoli(d)
    assert b["5 ore"]["pct"] == 0.0 and b["5 ore"]["reset"] == "appena azzerato"
    assert b["Settimana"]["pct"] == 30 and not d["vecchio"]


def test_dati_vecchi_oltre_10_minuti():
    d = plancia.descrivi_usage({"five_hour": None, "seven_day": {"pct": 30}, "ts": ORA - 15 * 60}, ORA)
    assert d["eta"] == "dati vecchi (15 min)" and d["vecchio"]
    assert "5 ore" not in titoli(d)   # niente falso 0% su dato vecchio


@pytest.mark.parametrize("usage", [None, {}, [], "x", 5])
def test_usage_assente_o_non_valido(usage):
    assert plancia.descrivi_usage(usage, ORA) is None


@pytest.mark.parametrize("pct", ["abc", None, True, float("nan"), [], {}])
def test_pct_non_numerico_senza_eccezioni(pct):
    d = plancia.descrivi_usage({"five_hour": {"pct": pct}, "seven_day": {"pct": pct}, "ts": ORA}, ORA)
    assert d["barre"] == []


def test_resets_at_nel_passato_e_valori_strani():
    d = plancia.descrivi_usage({"five_hour": {"pct": 120, "resets_at": ORA - 100}, "seven_day": {"pct": -5, "resets_at": "boh"}, "ts": ORA}, ORA)
    b = titoli(d)
    assert b["5 ore"]["pct"] == 100 and b["5 ore"]["reset"] == "reset appena avvenuto"
    assert b["Settimana"]["pct"] == 0 and b["Settimana"]["reset"] == "reset non noto"
    assert "100" in theme.barra_utilizzo("5 ore", b["5 ore"]["pct"], b["5 ore"]["reset"])


def test_ts_non_valido_non_solleva():
    assert plancia.descrivi_usage({"five_hour": {"pct": 5}, "ts": "x"}, ORA)["vecchio"]


def test_leggi_usage_file_mancante_vuoto_rotto(tmp_path):
    assert fonte.leggi_usage(tmp_path / "nonce.json") is None
    v = tmp_path / "vuoto.json"
    v.write_text("", encoding="utf-8")
    assert fonte.leggi_usage(v) is None
    r = tmp_path / "rotto.json"
    r.write_text("{\"five_hour\": nu", encoding="utf-8")
    assert fonte.leggi_usage(r) is None
    ok = tmp_path / "ok.json"
    ok.write_text('{"five_hour": null, "seven_day": {"pct": 4}, "ts": %f}' % ORA, encoding="utf-8")
    u = fonte.leggi_usage(ok)
    assert u["five_hour"] is None and plancia.descrivi_usage(u, ORA)["barre"][0]["titolo"] == "5 ore"


def test_leads_csv_mancante_cartella_vuota_e_csv_vuoto(tmp_path):
    assert clienti.leggi_leads(tmp_path / "non_esiste") == []
    assert clienti.leggi_leads(tmp_path) == []
    (tmp_path / "vuoto.csv").write_text("", encoding="utf-8")
    assert clienti.leggi_leads(tmp_path) == []
    (tmp_path / "solo_intestazione.csv").write_text("azienda,zona\n", encoding="utf-8")
    assert clienti.leggi_leads(tmp_path) == []


def test_scoperte_mancante_o_rotta(tmp_path):
    m = fonte.leggi_scoperte(tmp_path / "no.json")
    assert m["repo"] == [] and m["skill"] == [] and m["messaggio"]
    (tmp_path / "x.json").write_text("[1,", encoding="utf-8")
    assert fonte.leggi_scoperte(tmp_path / "x.json")["messaggio"]


def test_storico_cartella_non_scrivibile(tmp_path):
    file_al_posto_della_cartella = tmp_path / "blocco"
    file_al_posto_della_cartella.write_text("x", encoding="utf-8")
    assert storico.aggiungi({"ruolo": "user", "testo": "ciao"}, file_al_posto_della_cartella / "sotto") is False
    assert storico.carica_oggi(file_al_posto_della_cartella / "sotto") == []
    assert storico.elenco_giorni(file_al_posto_della_cartella / "sotto") == []


def test_chat_continua_con_storico_non_scrivibile(monkeypatch, tmp_path):
    """AppTest: salva_storico fallisce -> nessuna eccezione, avviso una sola volta."""
    from streamlit.testing.v1 import AppTest
    blocco = tmp_path / "blocco"
    blocco.write_text("x", encoding="utf-8")
    monkeypatch.setenv("GUARDIAN_CONV_DIR", str(blocco / "sotto"))
    at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception


def test_tool_result_doppio_non_solleva(tmp_path):
    """Regressione 26/11: due sessioni del browser leggevano le stesse righe → KeyError sul tool_use_id già consumato."""
    import json as _j
    import agenti
    p = tmp_path / "s.jsonl"
    righe = [{"type": "assistant", "timestamp": "2026-11-26T20:00:00Z", "message": {"content": [
                {"type": "tool_use", "id": "toolu_x", "name": "Read", "input": {"file_path": "a.py"}}]}},
             {"type": "user", "timestamp": "2026-11-26T20:00:01Z", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "toolu_x", "content": "ok"}]}}]
    p.write_text("\n".join(_j.dumps(r) for r in righe) + "\n", encoding="utf-8")
    st = agenti._Stato(p)
    st.aggiorna()
    for r in righe:      # stesse righe rilette (come faceva il secondo thread): nessuna eccezione
        st.feed(r)
