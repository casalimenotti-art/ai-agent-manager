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
