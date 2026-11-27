"""Voce: registrazione dal microfono del browser (st.audio_input) + riconoscimento vocale LOCALE con faster-whisper.

L'audio non lascia il PC. Solo la PRIMA volta il modello (circa 140 MB per "base") viene scaricato da Hugging Face.
Il testo riconosciuto va sempre mostrato e confermato dal titolare prima di inviarlo a Guardian.
"""
from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import threading
import wave

import config

PACCHETTO, VERSIONE = "faster-whisper", "1.2.1"
MAX_BYTES, MAX_SECONDI = 12 * 1024 * 1024, 120
_modelli: dict = {}
_LOCK_VOCE = threading.RLock()   # caricamento modelli e decodifica: una sessione alla volta


def disponibile() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def _vad_disponibile() -> bool:
    """Il filtro dei silenzi (VAD) di faster-whisper richiede onnxruntime, che non ha ancora wheel per ogni Python (es. 3.15)."""
    return importlib.util.find_spec("onnxruntime") is not None


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


def _carica(modello: str):
    with _LOCK_VOCE:
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
            with _LOCK_VOCE:   # i segmenti sono un generatore: va consumato dentro il lock
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
                 f"{PACCHETTO}=={VERSIONE}"])
    except (subprocess.TimeoutExpired, OSError) as e:
        return {"ok": False, "messaggio": f"Installazione non riuscita: {e}"}
    if r.returncode != 0:
        return {"ok": False, "messaggio": "Installazione non riuscita: " + (r.stderr.strip()[-250:] or "errore")}
    importlib.invalidate_caches()
    return {"ok": True, "messaggio": f"{PACCHETTO} {VERSIONE} installato. Il primo riconoscimento scarica il modello."}


# ---------------------------------------------------------------- Voce di Guardian (sintesi vocale)
import asyncio
import os
import re
import tempfile
from pathlib import Path

VOCE_EDGE = "it-IT-IsabellaNeural"
VOCE_SAPI = "Microsoft Elsa Desktop"
MAX_PARLATO = 1200
NOTA_VOCE = ("La voce Isabella invia il testo della risposta al servizio vocale Microsoft (edge-tts); "
             "Elsa è locale e non invia nulla. Se Isabella non risponde uso Elsa.")


def testo_parlabile(testo: str) -> str:
    """Toglie markdown, link e blocchi di codice: si legge solo il discorso."""
    t = re.sub(r"```.*?```", " ", str(testo or ""), flags=re.S)
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"[`*_#>|~]+", " ", t)
    t = re.sub(r"[\x00-\x1f\x7f]+", " ", t)
    return " ".join(t.split())[:MAX_PARLATO]


def _edge_reale(testo: str, voce: str = VOCE_EDGE) -> bytes:
    import edge_tts   # import tardivo: pacchetto opzionale

    async def _scarica() -> bytes:
        buf = bytearray()
        async for pezzo in edge_tts.Communicate(testo, voce).stream():
            if pezzo.get("type") == "audio":
                buf += pezzo["data"]
        return bytes(buf)

    return asyncio.run(asyncio.wait_for(_scarica(), timeout=20))


_PS_SINTESI = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $s.SelectVoice($env:GUARDIAN_TTS_VOICE) } catch {
  $it = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -eq 'it-IT' } | Select-Object -First 1
  if ($it) { $s.SelectVoice($it.VoiceInfo.Name) }
}
$s.SetOutputToWaveFile($env:GUARDIAN_TTS_OUT)
$s.Speak($env:GUARDIAN_TTS_TEXT)
$s.Dispose()
"""


def _powershell(script: str, env_extra: dict, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout, env={**os.environ, **env_extra})


def _sapi_reale(testo: str) -> bytes:
    """Sintesi locale Windows (System.Speech, voce Elsa) -> WAV."""
    with tempfile.TemporaryDirectory(prefix="guardian_tts_") as d:
        out = Path(d) / "voce.wav"
        r = _powershell(_PS_SINTESI, {"GUARDIAN_TTS_TEXT": testo, "GUARDIAN_TTS_VOICE": VOCE_SAPI, "GUARDIAN_TTS_OUT": str(out)})
        if r.returncode != 0 or not out.is_file():
            raise RuntimeError((r.stderr or "SAPI non disponibile").strip()[:160])
        return out.read_bytes()


def parla(testo: str, _edge=None, _sapi=None) -> dict:
    """Audio della voce di Guardian: {"ok","dati","mime","motore","messaggio"}.

    Prima edge-tts (it-IT-IsabellaNeural, online); se manca o fallisce, SAPI Windows (Elsa, locale, WAV).
    `_edge(testo) -> bytes` e `_sapi(testo) -> bytes` sono motori finti per i test."""
    t = testo_parlabile(testo)
    if not t:
        return {"ok": False, "dati": b"", "mime": "", "motore": "", "messaggio": "Niente da leggere."}
    errori = []
    try:
        dati = (_edge or _edge_reale)(t)
        if dati:
            return {"ok": True, "dati": dati, "mime": "audio/mpeg", "motore": "Isabella (edge-tts)", "messaggio": ""}
        errori.append("edge-tts: audio vuoto")
    except Exception as e:   # offline, pacchetto mancante, servizio non raggiungibile…
        errori.append(f"edge-tts: {type(e).__name__}")
    try:
        dati = (_sapi or _sapi_reale)(t)
        if dati:
            return {"ok": True, "dati": dati, "mime": "audio/wav", "motore": "Elsa (locale)", "messaggio": ""}
        errori.append("SAPI: audio vuoto")
    except Exception as e:
        errori.append(f"SAPI: {type(e).__name__}")
    return {"ok": False, "dati": b"", "mime": "", "motore": "", "messaggio": "Voce non disponibile (" + "; ".join(errori) + ")."}


# ---------------------------------------------------------------- Riconoscimento offline di Windows (System.Speech)
_PS_RICONOSCITORI = ("Add-Type -AssemblyName System.Speech; "
                     "[System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | ForEach-Object { $_.Culture.Name }")

_PS_RICONOSCI = r"""
Add-Type -AssemblyName System.Speech
$info = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | Where-Object { $_.Culture.Name -eq 'it-IT' } | Select-Object -First 1
if (-not $info) { [Console]::Error.WriteLine('NO_IT'); exit 3 }
$e = New-Object System.Speech.Recognition.SpeechRecognitionEngine($info)
$e.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$e.SetInputToWaveFile($env:GUARDIAN_STT_IN)
$out = @()
while ($true) { $r = $e.Recognize(); if (-not $r) { break }; $out += $r.Text }
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Output ($out -join ' ')
"""


def riconoscitori_windows(_runner=None) -> list[str]:
    """Culture dei riconoscitori vocali installati in Windows (es. ["it-IT"]); [] se nessuno o non Windows."""
    if _runner is None and os.name != "nt":
        return []
    try:
        r = (_runner or (lambda: _powershell(_PS_RICONOSCITORI, {}, 30)))()
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [x.strip() for x in (r.stdout or "").splitlines() if x.strip()] if r.returncode == 0 else []


def python_ok_per_whisper() -> bool:
    return (3, 11) <= sys.version_info[:2] <= (3, 13)


# ---------------------------------------------------------------- Sherpa-onnx (Parakeet TDT 0.6b v3 int8, offline, italiano)
NOME_MODELLO_SHERPA = "sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"
URL_MODELLO_SHERPA = ("https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/" + NOME_MODELLO_SHERPA + ".tar.bz2")
_sherpa: dict = {}


def cartella_modello_sherpa():
    return config.CLAUDE_HOME / "guardian" / "modelli" / NOME_MODELLO_SHERPA


def sherpa_pacchetto() -> bool:
    return importlib.util.find_spec("sherpa_onnx") is not None


def sherpa_modello() -> bool:
    d = cartella_modello_sherpa()
    return all((d / f).is_file() for f in ("encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt"))


def wav_a_mono16k(dati: bytes):
    """WAV (PCM 8/16/32 bit, qualsiasi canali/frequenza) -> (numpy float32 mono in [-1, 1], 16000)."""
    import numpy as np
    with wave.open(io.BytesIO(bytes(dati))) as w:
        n, ch, sw, fr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        grezzo = w.readframes(n)
    if sw == 2:
        x = np.frombuffer(grezzo, dtype="<i2").astype(np.float32) / 32768.0
    elif sw == 1:
        x = (np.frombuffer(grezzo, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif sw == 4:
        x = np.frombuffer(grezzo, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"WAV a {sw * 8} bit non supportato")
    if ch > 1:
        x = x[: len(x) // ch * ch].reshape(-1, ch).mean(axis=1)
    if fr != 16000 and len(x) > 1:
        m = int(round(len(x) * 16000 / fr))
        x = np.interp(np.linspace(0, len(x) - 1, m), np.arange(len(x)), x).astype(np.float32)
    return x.astype(np.float32), 16000


def _riconoscitore_sherpa():
    with _LOCK_VOCE:
        if "r" not in _sherpa:
            import sherpa_onnx   # import tardivo: pesante
            d = cartella_modello_sherpa()
            _sherpa["r"] = sherpa_onnx.OfflineRecognizer.from_transducer(
                encoder=str(d / "encoder.int8.onnx"), decoder=str(d / "decoder.int8.onnx"), joiner=str(d / "joiner.int8.onnx"),
                tokens=str(d / "tokens.txt"), num_threads=4, model_type="nemo_transducer")
        return _sherpa["r"]


def trascrivi_sherpa(dati: bytes, _riconoscitore=None) -> dict:
    """Riconoscimento offline con sherpa-onnx. Stesso formato di trascrivi(). `_riconoscitore` finto per i test."""
    ok, msg = valida_wav(dati)
    if not ok:
        return {"ok": False, "testo": "", "messaggio": msg}
    try:
        campioni, sr = wav_a_mono16k(dati)
        rec = _riconoscitore or _riconoscitore_sherpa()
        with _LOCK_VOCE:
            flusso = rec.create_stream()
            flusso.accept_waveform(sr, campioni)
            rec.decode_stream(flusso)
            testo = flusso.result.text
    except Exception as e:
        return {"ok": False, "testo": "", "messaggio": f"Riconoscimento non riuscito: {type(e).__name__}: {str(e)[:160]}"}
    testo = " ".join(str(testo).split())
    if not testo:
        return {"ok": False, "testo": "", "messaggio": "Non ho sentito parole: riprova più vicino al microfono."}
    return {"ok": True, "testo": testo[:4000], "messaggio": ""}


def motore_riconoscimento(_riconoscitori=None) -> dict:
    """Quale riconoscimento LOCALE c'è: {"motore": "sherpa"|"whisper"|"windows"|None, "mancante": spiegazione se None}."""
    if sherpa_pacchetto() and sherpa_modello():
        return {"motore": "sherpa", "mancante": ""}
    if disponibile():
        return {"motore": "whisper", "mancante": ""}
    cult = riconoscitori_windows() if _riconoscitori is None else _riconoscitori
    if any(c.lower().startswith("it") for c in cult):
        return {"motore": "windows", "mancante": ""}
    py = (f"Python {sys.version_info.major}.{sys.version_info.minor}: faster-whisper richiede 3.11-3.13"
          if not python_ok_per_whisper() else "installa faster-whisper dal pulsante qui sotto")
    nota = ""
    if sherpa_pacchetto() and not sherpa_modello():
        nota = f"Per sherpa-onnx manca il modello: scarica {URL_MODELLO_SHERPA} ed estrailo in {cartella_modello_sherpa().parent}. "
    elif not sherpa_pacchetto() and sherpa_modello():
        nota = "Per sherpa-onnx manca il pacchetto: pip install sherpa-onnx. "
    return {"motore": None, "mancante": nota + "Nessun riconoscimento vocale locale. Servono: " + py + ", oppure il pacchetto vocale italiano di "
            "Windows (Impostazioni > Ora e lingua > Lingua e area geografica > Italiano > Opzioni lingua > Voce)"
            + (f". Riconoscitori Windows installati ora: {', '.join(cult)}." if cult else ".")}


def trascrivi_windows(dati: bytes, _runner=None) -> dict:
    """Riconoscimento offline di Windows (it-IT). Stesso formato di trascrivi()."""
    ok, msg = valida_wav(dati)
    if not ok:
        return {"ok": False, "testo": "", "messaggio": msg}
    try:
        with tempfile.TemporaryDirectory(prefix="guardian_stt_") as d:
            f = Path(d) / "in.wav"
            f.write_bytes(bytes(dati))
            r = (_runner or (lambda p: _powershell(_PS_RICONOSCI, {"GUARDIAN_STT_IN": str(p)}, 90)))(f)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "testo": "", "messaggio": f"Riconoscimento di Windows non riuscito: {type(e).__name__}"}
    if r.returncode == 3 or "NO_IT" in (r.stderr or ""):
        return {"ok": False, "testo": "", "messaggio": "Windows non ha un riconoscitore italiano installato."}
    if r.returncode != 0:
        return {"ok": False, "testo": "", "messaggio": "Riconoscimento di Windows non riuscito: " + (r.stderr or "errore").strip()[:160]}
    testo = " ".join((r.stdout or "").split())
    if not testo:
        return {"ok": False, "testo": "", "messaggio": "Non ho sentito parole: riprova più vicino al microfono."}
    return {"ok": True, "testo": testo[:4000], "messaggio": ""}


def trascrivi_locale(dati: bytes, motore: str) -> dict:
    if motore == "sherpa":
        return trascrivi_sherpa(dati)
    return trascrivi(dati) if motore == "whisper" else trascrivi_windows(dati)
