import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import theme


def test_css_senza_caratteri_di_controllo():
    # Un "\25CF" scritto in una stringa Python normale diventa \x15 + "CF": nel browser compariva "CF"/"D0".
    css = theme.CSS + theme.CSS_EXTRA + theme.CSS_PLANCIA
    assert not [hex(ord(c)) for c in css if ord(c) < 32 and c not in "\n\r\t"]


def test_css_mobile_e_reduced_motion():
    css = theme.CSS_PLANCIA.replace(" ", "")
    assert "@media(max-width:900px)" in css
    assert "prefers-reduced-motion" in css


def test_storico_chat_ancorato_e_allineato_in_alto():
    # Regressione: la risposta di Guardian finiva fuori vista.
    righe = [r.replace(" ", "") for r in theme.CSS_PLANCIA.splitlines() if "st-key-chat_storico" in r]
    assert any("column-reverse" in r and "justify-content:flex-start" in r for r in righe)


def test_css_mobile_mic_e_storico():
    css = theme.CSS_PLANCIA.replace(" ", "")
    assert 'st-key-mic_pop' in css and "min-height:52px" in css and "Parlaconguardian" not in css
    assert "Parla con Guardian" in theme.CSS_PLANCIA
    assert "height:45vh!important" in css
