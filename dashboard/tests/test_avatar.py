import avatar


def test_comandi_locali():
    assert avatar.comando_da_testo("Guardian, guarda a destra!") == {"azione": "guarda", "dir": "destra"}
    assert avatar.comando_da_testo("guarda giù") == {"azione": "guarda", "dir": "giu"}
    assert avatar.comando_da_testo("Vieni al centro") == {"azione": "centro"}
    assert avatar.comando_da_testo("Dimmi come si dice saluta") is None


def test_visuale_stato_e_movimento():
    assert 'data-movimento="destra"' in avatar.visuale("ascolto", {"dir": "destra"})
    assert "In ascolto" in avatar.visuale("ascolto")
    assert "onload" not in avatar.visuale("onload", {"dir": "onload"})


def test_modello_webgl_locale():
    html = avatar.modello()
    assert 'getContext("webgl"' in html
    assert 'g-parla' in html
    assert '<script src=' not in html


def test_ritratto_locale_con_pointer_e_motion_ridotto():
    html = avatar.ritratto()
    assert "data:image/jpeg;base64,/9j/" in html
    assert "__PORTRAIT__" not in html
    assert "pointermove" in html and "prefers-reduced-motion" in html
    assert "texture2D(picture,clamp(p-turn" in html
