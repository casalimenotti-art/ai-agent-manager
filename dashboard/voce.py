"""Voce: registrazione dal microfono del browser (st.audio_input) + riconoscimento vocale LOCALE con faster-whisper.

L'audio non lascia il PC. Solo la PRIMA volta il modello (circa 140 MB per "base") viene scaricato da Hugging Face.
Il testo riconosciuto va sempre mostrato e confermato dal titolare prima di inviarlo a Guardian.
"""
from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import wave

import config

PACCHETTO, VERSIONE = "faster-whisper", "1.2.1"
MAX_BYTES, MAX_SECONDI = 12 * 1024 * 1024, 120
_modelli: dict = {}


def disponibile() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def valida_wav(dati: bytes) -> tuple[bool, str]:
    if not isinstance(dati, (bytes, bytearray)) or len(dati) < 64:
        return False, "Registrazione vuota."
    if len(dati) > MAX_BYTES:
        return False, "Registrazione troppo lunga."
    try:
        with wave.open(io.BytesIO(bytes(dati))) as w:
            durata = w.getnframes() / float(w.getframerate() or 1)
    except (wave.Error, EOFError):
        return False, "Formato audio non valido (atteso WAV)."
    if durata < 0.3:
        return False, "Registrazione troppo breve."
    if durata > MAX_SECONDI:
        return False, f"Registrazione oltre {MAX_SECONDI} secondi: dividila in parti."
    return True, ""


def _vad_disponibile() -> bool:
    """Il filtro delle pause di faster-whisper richiede onnxruntime (su alcune versioni di Python non ha ancora i pacchetti)."""
    return importlib.util.find_spec("onnxruntime") is not None


def _carica(modello: str):
    if modello not in _modelli:
        from faster_whisper import WhisperModel   # import tardivo: pesante
        _modelli[modello] = WhisperModel(modello, device="cpu", compute_type="int8")
    return _modelli[modello]


def trascrivi(dati: bytes, lingua: str = "it", modello: str | None = None, _motore=None) -> dict:
    """{"ok", "testo", "messaggio"}. `_motore(dati, lingua) -> str` serve ai test."""
    ok, msg = valida_wav(dati)
    if not ok:
        return {"ok": False, "testo": "", "messaggio": msg}
    try:
        if _motore:
            testo = _motore(dati, lingua)
        else:
            if not disponibile():
                return {"ok": False, "testo": "", "messaggio": "Riconoscimento vocale non installato."}
            segmenti, _ = _carica(modello or config.WHISPER_MODEL).transcribe(io.BytesIO(bytes(dati)), language=lingua, vad_filter=_vad_disponibile())
            testo = " ".join(s.text.strip() for s in segmenti)
    except Exception as e:   # modello non scaricabile, audio illeggibile, memoria…
        return {"ok": False, "testo": "", "messaggio": f"Riconoscimento non riuscito: {type(e).__name__}: {str(e)[:160]}"}
    testo = " ".join(testo.split())
    if not testo:
        return {"ok": False, "testo": "", "messaggio": "Non ho sentito parole: riprova più vicino al microfono."}
    return {"ok": True, "testo": testo[:4000], "messaggio": ""}


def installa(runner=None) -> dict:
    """pip install del pacchetto, versione fissata e solo wheel, nell'ambiente di Guardian."""
    run = runner or (lambda cmd: subprocess.run(cmd, capture_output=True, text=True, timeout=900))
    try:
        r = run([sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check", "--only-binary=:all:",
                 f"{PACCHETTO}=={VERSIONE}", "av<19"])   # av 19 rompe faster-whisper 1.2.1 (verificato sul PC del titolare)
    except (subprocess.TimeoutExpired, OSError) as e:
        return {"ok": False, "messaggio": f"Installazione non riuscita: {e}"}
    if r.returncode != 0:
        return {"ok": False, "messaggio": "Installazione non riuscita: " + (r.stderr.strip()[-250:] or "errore")}
    importlib.invalidate_caches()
    return {"ok": True, "messaggio": f"{PACCHETTO} {VERSIONE} installato. Il primo riconoscimento scarica il modello."}
