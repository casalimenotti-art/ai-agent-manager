import pathlib, sys
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import plancia

ADESSO = datetime(2026, 11, 26, 15, 0).timestamp()
MEZZANOTTE = datetime(2026, 11, 26, 0, 0).timestamp()


def test_conteggi_e_ultimo():
    ev = [{"tipo": "file", "testo": "a.py", "ts": ADESSO - 60}, {"tipo": "file", "testo": "a.py", "ts": ADESSO - 30},
          {"tipo": "file", "testo": "b.py", "ts": ADESSO - 10}, {"tipo": "web-ricerca", "ts": ADESSO - 5},
          {"tipo": "web-apri", "ts": ADESSO - 5}]
    ag = [{"stato": "finito", "tipo": "subagente", "nome_agente": "web-designer", "compito": "Sito", "ultimo_agg": ADESSO - 600},
          {"stato": "finito", "tipo": "subagente", "nome_agente": "ricercatore-web", "compito": "Idee", "ultimo_agg": ADESSO - 1200},
          {"stato": "al lavoro", "ultimo_agg": ADESSO - 5}]
    r = plancia.riepilogo_oggi(ev, ag, ADESSO)
    assert (r["finiti"], r["file"], r["ricerche"]) == (2, 2, 1)
    assert r["ultimo"] == {"nome": "Web designer", "compito": "Sito", "minuti": 10}


def test_cambio_giorno_a_mezzanotte():
    ev = [{"tipo": "file", "testo": "ieri.py", "ts": MEZZANOTTE - 1}, {"tipo": "web-ricerca", "ts": MEZZANOTTE - 1},
          {"tipo": "web-ricerca", "ts": MEZZANOTTE}]
    ag = [{"stato": "finito", "ultimo_agg": MEZZANOTTE - 1}]
    r = plancia.riepilogo_oggi(ev, ag, MEZZANOTTE + 60)
    assert (r["finiti"], r["file"], r["ricerche"], r["ultimo"]) == (0, 0, 1, None)


def test_liste_vuote():
    assert plancia.riepilogo_oggi([], [], ADESSO) == {"finiti": 0, "file": 0, "ricerche": 0, "ultimo": None}
    assert plancia.riepilogo_oggi(None, None)["finiti"] == 0
    assert plancia.riepilogo_oggi([{}], [{}], ADESSO)["file"] == 0
