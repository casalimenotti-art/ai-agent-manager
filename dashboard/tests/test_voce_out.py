import json, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import voce_out as v


def test_pulizia_markdown_codice_tabelle_url():
    t = ("# Titolo\n\nHo **trovato** 3 clienti: vedi [la scheda](https://x.it/a) e https://y.it/z.\n\n"
         "```python\nprint('non leggere')\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n- primo punto\n- secondo `codice`")
    p = v.pulisci_per_voce(t)
    assert "non leggere" not in p and "|" not in p and "http" not in p and "il link" in p and "**" not in p and "`" not in p and "#" not in p
    assert "la scheda" in p and "Ho trovato 3 clienti" in p and "primo punto." in p and "secondo codice." in p


def test_fence_non_chiusa_viene_tagliata():
    assert "segreto" not in v.pulisci_per_voce("Ecco il comando.\n```bash\nrm -rf segreto")
    assert v.pulisci_per_voce("Ecco il comando.\n```bash\nrm") == "Ecco il comando."


def test_spezza_frasi_e_frasi_lunghe():
    assert v.spezza("Ciao a tutti. Come stai? Bene!") == ["Ciao a tutti.", "Come stai?", "Bene!"]
    lunga = ("parola, " * 80).strip()
    pezzi = v.spezza(lunga)
    assert len(pezzi) > 1 and all(len(p) <= 222 for p in pezzi) and " ".join(pezzi).replace(" ", "").replace(",", "") == lunga.replace(" ", "").replace(",", "")


def test_streaming_dice_solo_frasi_complete_una_volta():
    pieno = "Ho trovato tre clienti a Cagliari. Il primo è un ristorante senza sito. Il secondo"
    f1, parlato = v.prossimo_pezzo(v.pulisci_per_voce(pieno), "")
    assert f1 == ["Ho trovato tre clienti a Cagliari.", "Il primo è un ristorante senza sito."] and "secondo" not in " ".join(f1)
    f2, parlato2 = v.prossimo_pezzo(v.pulisci_per_voce(pieno), parlato)
    assert f2 == [] and parlato2 == parlato                                    # niente ripetizioni
    completo = pieno + " è un B&B con le prenotazioni solo al telefono."
    f3, _ = v.prossimo_pezzo(v.pulisci_per_voce(completo), parlato, finale=True)
    assert f3 == ["Il secondo è un B&B con le prenotazioni solo al telefono."]


def test_streaming_frase_troppo_corta_aspetta():
    assert v.prossimo_pezzo("Ok. ", "")[0] == []
    assert v.prossimo_pezzo("Ok. ", "", finale=True)[0] == ["Ok."]


def test_js_parla_escape_e_struttura():
    h = v.js_parla(["Dico </script><script>alert(1)</script>", "L'apostrofo \"e\" virgolette"])
    assert h.count("</script>") == 1 and "<\\/script>" in h                      # la chiusura dentro i dati è neutralizzata
    assert "window.parent" in h and "SpeechSynthesisUtterance" in h and "guardian_voce" in h
    dati = re.search(r"const frasi=(\[.*?\]);let prefs", h, re.S).group(1).replace("<\\/", "</")
    assert json.loads(dati)[1] == "L'apostrofo \"e\" virgolette"
    assert "cancel" in v.js_ferma()


def test_pannello_impostazioni_ha_i_controlli():
    h = v.html_impostazioni()
    for x in ("id='voce'", "id='rate'", "id='pitch'", "Prova la voce", "id='stop'", "localService", "online"):
        assert x in h


def test_link_non_lasciano_frasi_monche():
    assert v.pulisci_per_voce("Vedi https://a.it/x per la prova.") == "Vedi il link per la prova."
    assert "il link il link" not in v.pulisci_per_voce("Fonti: https://a.it https://b.it https://c.it")


def test_pannello_preseleziona_la_voce_consigliata():
    h = v.html_impostazioni()
    assert "function scegliVoce" in h and "const d=scegliVoce(S,prefs);if(d)sel.value=d.name" in h


def test_segnale_lavoro_e_decodifica_mic():
    assert "__guardianLavora=Date.now()" in v.js_lavora(True) and "__guardianLavora=0" in v.js_lavora(False)
    import base64, mic
    ok = base64.b64encode(b"RIFFxxxx").decode()
    assert mic.decodifica({"wav": ok}) == b"RIFFxxxx"
    assert mic.decodifica({"wav": "non base64!!"}) == b"" and mic.decodifica({"wav": 5}) == b""
    assert mic.decodifica({"wav": "A" * (13 * 1024 * 1024 * 4 // 3)}) == b""            # troppo grande


def test_js_parla_neutralizza_sequenze_pericolose():
    h = v.js_parla(["a <!-- b <script> c </script> d   e"])
    corpo = h.split("const frasi=", 1)[1].split(";let prefs", 1)[0]
    assert "<!--" not in corpo and "</" not in corpo and " " not in corpo


def test_adattatore_frame_ripiega_su_iframe(monkeypatch):
    import frame, streamlit as st, types
    visti = []
    monkeypatch.setattr(frame, "_c", types.SimpleNamespace())                 # components.html "rimosso"
    monkeypatch.setattr(st, "iframe", lambda html, height: visti.append((html, height)), raising=False)
    frame.html_frame("<b>x</b>", height=0)
    assert visti == [("<b>x</b>", 1)]
