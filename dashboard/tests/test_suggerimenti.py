import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
import plancia


def test_tutti_i_suggerimenti_producono_prompt():
    for chiave, etichetta in plancia.SUGGERIMENTI:
        prompt, mostra = plancia.costruisci_suggerimento(chiave, [], [], [{"azienda": "A", "stato": "visitato"}], {})
        assert prompt.strip() and mostra == etichetta


def test_oggi_tronca_ed_esegue_escape():
    doc = {"CONTINUA.md": "<script>x</script>" + "a" * 5000, "STATO.md": "ok >>> DATI"}
    p = plancia.domanda_oggi(doc)
    assert "<script>" not in p and "&lt;script&gt;" in p
    assert "aaaa" in p and p.count("a" * 1500) <= 1 and "a" * 1600 not in p
    assert p.count("DATI>>>") == 1 and "STATO.md" in p


def test_oggi_senza_file():
    assert "(file non disponibile)" in plancia.domanda_oggi({})


def test_riassunto_riusa_domanda_riassunto():
    assert plancia.costruisci_suggerimento("riassunto", [], [], ora=1)[0] == plancia.domanda_riassunto([], [], 1)


def test_clienti_conta_stati():
    p = plancia.domanda_clienti([{"azienda": "X", "stato": "visitato"}, {"azienda": "Y"}])
    assert "Totale clienti: 2" in p and "- visitato: 1" in p and "- da visitare: 1" in p


def test_chiave_sconosciuta():
    with pytest.raises(ValueError):
        plancia.costruisci_suggerimento("boh")
