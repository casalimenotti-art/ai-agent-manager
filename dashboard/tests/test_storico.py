import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import storico


def test_salva_e_ricarica(tmp_path):
    c = tmp_path / "conv"
    assert storico.aggiungi({"ruolo": "user", "testo": "ciao"}, c)
    assert storico.aggiungi({"ruolo": "assistant", "testo": "ok <system-reminder>segreto</system-reminder> fine"}, c)
    m = storico.carica_oggi(c)
    assert [x["ruolo"] for x in m] == ["user", "assistant"]
    assert "segreto" not in m[1]["testo"] and "ts" in m[0]


def test_riga_malformata(tmp_path):
    storico.aggiungi({"ruolo": "user", "testo": "uno"}, tmp_path)
    f = tmp_path / f"{date.today().isoformat()}.jsonl"
    with open(f, "a", encoding="utf-8") as fh:
        fh.write("{rotto\n[1,2]\n" + json.dumps({"ruolo": "x", "testo": "no"}) + "\n")
    assert [x["testo"] for x in storico.carica_oggi(tmp_path)] == ["uno"]


def test_limite(tmp_path):
    for i in range(10):
        storico.aggiungi({"ruolo": "user", "testo": f"m{i}"}, tmp_path)
    m = storico.carica_oggi(tmp_path, limite=3)
    assert [x["testo"] for x in m] == ["m7", "m8", "m9"]


def test_elenco_giorni(tmp_path):
    (tmp_path / "2026-01-02.jsonl").write_text(json.dumps({"ruolo": "user", "testo": "a", "ts": 1}) + "\n", encoding="utf-8")
    (tmp_path / "2026-03-04.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "altro.jsonl").write_text("", encoding="utf-8")
    assert storico.elenco_giorni(tmp_path) == ["2026-03-04", "2026-01-02"]
    assert storico.carica_giorno("2026-01-02", tmp_path)[0]["testo"] == "a"
    assert storico.carica_giorno("../x", tmp_path) == []
    assert storico.elenco_giorni(tmp_path / "manca") == []
