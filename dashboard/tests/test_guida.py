from pathlib import Path

import plancia

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_guida_cita_gli_spazi():
    src = Path(APP).read_text(encoding="utf-8")
    titoli = [t for t in ("Agenti", "Skill", "Squadra", "Store", "Clienti", "Siti demo", "Scoperte")]
    for t in titoli:
        assert f'"{t}"' in src
        assert t in plancia.GUIDA
    assert len(plancia.GUIDA.strip().splitlines()) <= 15


def test_guida_comandi_esistono():
    for frase in ("riassunto agenti", "nuova conversazione", "voce on", "apri agenti"):
        assert plancia.riconosci_comando("Guardian, " + frase)


def test_guida_apre_senza_eccezioni():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    [b for b in at.sidebar.button if b.key == "sb_guida"][0].click().run()
    assert not at.exception
