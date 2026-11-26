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
