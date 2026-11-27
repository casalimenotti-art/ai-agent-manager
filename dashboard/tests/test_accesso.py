import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import accesso


def test_host_locali():
    for h in ("localhost", "localhost:8501", "127.0.0.1", "127.0.0.1:8501", "[::1]", "[::1]:8501", "LOCALHOST"):
        assert accesso.host_locale(h), h


def test_host_remoti():
    for h in ("pc.tail1234.ts.net", "pc.tail1234.ts.net:443", "192.168.1.5:8501", "", None, "localhost.evil.com"):
        assert not accesso.host_locale(h), h


def test_hash_corretto_ed_errato():
    h = accesso.crea_hash("123456")
    assert h.startswith("pbkdf2_sha256$200000$") and "123456" not in h
    assert accesso.verifica_pin("123456", h)
    assert not accesso.verifica_pin("654321", h)
    assert accesso.crea_hash("123456") != h  # sale casuale


def test_formato_rotto_o_assente():
    for h in ("", None, "abc", "md5$1$aa$bb", "pbkdf2_sha256$x$zz$yy", "pbkdf2_sha256$1$aa"):
        assert not accesso.verifica_pin("123456", h)


def test_attesa_crescente():
    assert accesso.attesa_dopo(0) == 0
    assert accesso.attesa_dopo(2) > accesso.attesa_dopo(1)
    assert accesso.attesa_dopo(5) == 300


def _pagina_remota():
    import streamlit as st
    import accesso

    class _Ctx:
        headers = {"Host": "pc.tail1234.ts.net"}

    class _St:
        context = _Ctx()

        def __getattr__(self, n):
            return getattr(st, n)

    accesso.richiedi_pin(_St())
    st.write("CONTENUTO_PRIVATO")


def test_schermata_pin_remota(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("GUARDIAN_PIN_HASH", accesso.crea_hash("123456"))
    at = AppTest.from_function(_pagina_remota).run()
    assert not at.exception
    assert any("accesso" in m.value for m in at.markdown)
    assert len(at.text_input) == 1 and not any("CONTENUTO_PRIVATO" in m.value for m in at.markdown)
    at.text_input[0].set_value("000000"); at.button[0].click(); at.run()
    assert at.error and not any("CONTENUTO_PRIVATO" in m.value for m in at.markdown)
    assert at.session_state["_pin_fino"] > 0  # attesa attiva dopo l'errore
    at.session_state["_pin_fino"] = 0.0
    at.run()
    at.text_input[0].set_value("123456"); at.button[0].click(); at.run()
    at.run()
    assert any("CONTENUTO_PRIVATO" in m.value for m in at.markdown)


def test_remoto_senza_hash(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.delenv("GUARDIAN_PIN_HASH", raising=False)
    monkeypatch.delenv("GUARDIAN_PIN_OSPITI_HASH", raising=False)
    at = AppTest.from_function(_pagina_remota).run()
    assert "non configurato" in at.error[0].value
    assert not any("CONTENUTO_PRIVATO" in m.value for m in at.markdown)


def test_proxy_conta_come_remoto():
    """tailscale serve inoltra a 127.0.0.1: senza questo controllo il PIN verrebbe saltato."""
    import accesso
    assert accesso.passa_da_proxy({"Host": "127.0.0.1:8501", "X-Forwarded-For": "100.64.0.2"})
    assert accesso.passa_da_proxy({"host": "localhost:8501", "Tailscale-User-Login": "a@b.c"})
    assert not accesso.passa_da_proxy({"Host": "localhost:8501", "User-Agent": "x"})
