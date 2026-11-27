"""Accesso remoto: blocco con PIN (logica pura + schermata). Il PIN non e' mai salvato in chiaro."""
import hashlib
import hmac
import os
import secrets
import time

ITERAZIONI = 200000
MAX_TENTATIVI = 5
BLOCCO_SEC = 300
_LOCALI = {"localhost", "127.0.0.1", "[::1]", "::1"}


def host_locale(host) -> bool:
    """True se l'Host della richiesta e' il PC stesso (con o senza porta)."""
    h = (host or "").strip().lower()
    if not h:
        return False
    if h.startswith("["):
        h = h.split("]")[0] + "]"
    elif h.count(":") == 1:
        h = h.split(":")[0]
    return h in _LOCALI


_INTESTAZIONI_PROXY = ("x-forwarded-for", "x-forwarded-host", "x-forwarded-proto", "forwarded",
                       "tailscale-user-login", "tailscale-user-name", "x-real-ip", "cf-connecting-ip")


def passa_da_proxy(headers) -> bool:
    """True se la richiesta arriva tramite un proxy (tailscale serve, tunnel): allora non e' 'dal PC'."""
    try:
        chiavi = {str(k).lower() for k in headers.keys()}
    except Exception:
        return False
    return any(h in chiavi for h in _INTESTAZIONI_PROXY)


def crea_hash(pin: str) -> str:
    sale = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), sale, ITERAZIONI)
    return f"pbkdf2_sha256${ITERAZIONI}${sale.hex()}${h.hex()}"


def verifica_pin(pin: str, hash_salvato) -> bool:
    try:
        schema, it, sale, atteso = (hash_salvato or "").strip().split("$")
        if schema != "pbkdf2_sha256":
            return False
        calc = hashlib.pbkdf2_hmac("sha256", (pin or "").encode("utf-8"), bytes.fromhex(sale), int(it))
        return hmac.compare_digest(calc, bytes.fromhex(atteso))
    except (ValueError, TypeError, AttributeError):
        return False


def ruolo_pin(pin: str, hash_titolare, hash_ospiti) -> str | None:
    """'titolare' (accesso completo), 'ospite' (sola lettura) o None se il PIN e' sbagliato."""
    if hash_titolare and verifica_pin(pin, hash_titolare):
        return "titolare"
    if hash_ospiti and verifica_pin(pin, hash_ospiti):
        return "ospite"
    return None


def e_ospite(st) -> bool:
    """True se chi guarda e' entrato con il PIN ospiti: niente chat, niente lanci, niente modifiche."""
    try:
        return bool(st.session_state.get("_ospite"))
    except Exception:
        return False


def attesa_dopo(sbagliati: int) -> int:
    """Secondi di attesa dopo N tentativi sbagliati consecutivi (crescente, poi blocco)."""
    if sbagliati >= MAX_TENTATIVI:
        return BLOCCO_SEC
    return 0 if sbagliati <= 0 else 2 ** (sbagliati - 1)


def richiedi_pin(st) -> None:
    """Se l'accesso e' remoto, mostra la schermata PIN e ferma la pagina finche' il PIN non e' giusto."""
    try:
        headers = st.context.headers
        host = headers.get("Host")
        via_proxy = passa_da_proxy(headers)
    except Exception:
        host, via_proxy = None, False
    # Host assente = nessuna richiesta HTTP reale (test/bare mode): un browser lo invia sempre.
    # Dietro un proxy (tailscale serve, tunnel) l'Host puo' sembrare localhost: conta come remoto.
    if st.session_state.get("_pin_ok") or (not via_proxy and (host is None or host_locale(host))):
        return
    hash_salvato = os.environ.get("GUARDIAN_PIN_HASH", "").strip()
    hash_ospiti = os.environ.get("GUARDIAN_PIN_OSPITI_HASH", "").strip()
    st.markdown("<div class='gd-accesso'><h2>Guardian · accesso</h2></div>", unsafe_allow_html=True)
    if not hash_salvato and not hash_ospiti:
        st.error("Accesso remoto non configurato: imposta il PIN sul PC con dashboard\\telefono\\imposta-pin.bat")
        st.stop()
    ora = time.time()
    fino = st.session_state.get("_pin_fino", 0.0)
    if ora < fino:
        st.warning(f"Troppi tentativi. Riprova tra {int(fino - ora) + 1} secondi.")
        st.stop()
    with st.form("gd_pin"):
        pin = st.text_input("PIN", type="password")
        invia = st.form_submit_button("Entra")
    if invia:
        ruolo = ruolo_pin(pin, hash_salvato, hash_ospiti)
        if ruolo:
            st.session_state["_pin_ok"] = True
            st.session_state["_ospite"] = ruolo == "ospite"
            st.session_state["_pin_err"] = 0
            st.rerun()
        n = st.session_state.get("_pin_err", 0) + 1
        st.session_state["_pin_err"] = n
        att = attesa_dopo(n)
        st.session_state["_pin_fino"] = time.time() + att
        if n >= MAX_TENTATIVI:
            st.session_state["_pin_err"] = 0
            st.error("PIN errato. Troppi tentativi: accesso bloccato per 5 minuti.")
        else:
            st.error(f"PIN errato ({n}/{MAX_TENTATIVI}). Attendi {att} s.")
    st.stop()
