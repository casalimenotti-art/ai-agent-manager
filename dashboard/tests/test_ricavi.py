import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
import config, monitor


@pytest.fixture(autouse=True)
def cartella(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "EVENTS_FILE", tmp_path / "g" / "events.jsonl")


def test_scrive_e_rilegge():
    assert monitor.leggi_ricavi() == {}
    monitor.scrivi_ricavo("2026-11", 1234.5)
    monitor.scrivi_ricavo("2026-10", 10)
    assert monitor.leggi_ricavi() == {"2026-11": 1234.5, "2026-10": 10.0}


@pytest.mark.parametrize("mese,importo", [("2026-13", 1), ("26-11", 1), ("../x", 1), ("2026-11", -1),
                                           ("2026-11", float("nan")), ("2026-11", float("inf")), ("2026-11", "5")])
def test_rifiuta_input_non_valido(mese, importo):
    with pytest.raises(ValueError):
        monitor.scrivi_ricavo(mese, importo)


def test_file_corrotto_ignorato():
    monitor._file_ricavi().parent.mkdir(parents=True)
    monitor._file_ricavi().write_text("{rotto")
    assert monitor.leggi_ricavi() == {}
