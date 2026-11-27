import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
import siti_demo as sd


@pytest.mark.parametrize("cat,chiave", [("ristorante", "ristorante"), ("Trattoria", "ristorante"), ("B&B", "b&b"), ("Casa vacanze", "b&b"),
                                        ("ottica", "ottica"), ("Parrucchiere", "parrucchiere"), ("officina", "officina"),
                                        ("studio professionale", "studio"), ("boh", "generico"), ("", "generico")])
def test_categorie(cat, chiave):
    assert sd.categoria_chiave(cat) == chiave


@pytest.mark.parametrize("cat", ["ristorante", "b&b", "ottica", "parrucchiere", "officina", "studio", "altro"])
@pytest.mark.parametrize("tema", ["notte", "caldo", "mare", "inesistente"])
def test_pagina_autonoma_senza_rete(cat, tema):
    h = sd.genera_sito("Bar Sole", cat, "Cagliari", tema)
    assert h.startswith("<!doctype html>") and "<html lang='it'>" in h and "viewport" in h
    assert not re.search(r"(src|href)=['\"]https?://|url\(\s*['\"]?https?://|@import|<script", h, re.I)   # nessuna risorsa esterna, nessun JS
    assert "da inserire" in h and "prefers-reduced-motion" in h


def test_escape_di_input_ostili():
    h = sd.genera_sito("<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "\"><b>", "notte", "<i>x</i>")
    assert "<script>alert" not in h and "<img src=x" not in h and "<b>" not in h and "<i>x" not in h
    assert "&lt;script&gt;" in h


def test_ottica_ha_la_prova_virtuale_ma_senza_inventare_dati():
    h = sd.genera_sito("Ottica Demo", "ottica", "Cagliari")
    assert "Provali da casa" in h and "sul tuo dispositivo" in h
    assert not re.search(r"\+39|\d{2}:\d{2}|€|\d{3}[ -]?\d{6,7}", h)       # nessun telefono, orario o prezzo inventato


def test_nome_vuoto_e_lungo():
    assert "La tua attività" in sd.genera_sito("", "bar", "")
    assert len(sd.genera_sito("x" * 500, "bar", "y" * 500)) < 20000
    assert sd.slug_file("Bar  Sole!!") == "bar-sole" and sd.slug_file("") == "sito"


def test_pagina_preferisce_il_sito_salvato(tmp_path):
    import siti_demo as sd
    html, salvato = sd.pagina(tmp_path, "Bar Uno", "bar", "Cagliari")
    assert not salvato and "Bar Uno" in html
    (tmp_path / "bar-uno.html").write_text("<p>personalizzato</p>", encoding="utf-8")
    html, salvato = sd.pagina(tmp_path, "Bar Uno", "bar", "Cagliari")
    assert salvato and html == "<p>personalizzato</p>"
