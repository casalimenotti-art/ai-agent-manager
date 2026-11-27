"""Servizio vocale LOCALE per Guardian HQ: trascrive l'audio con sherpa-onnx + Parakeet sul PC, senza internet.

  python bridge/guardian_bridge.py voce          (oppure: python bridge/voce_locale.py)

- Ascolta SOLO su 127.0.0.1 (mai sulla rete). Nessun comando eseguibile: riceve audio WAV e restituisce testo.
- Accetta solo le origini dell'HQ (GUARDIAN_HQ_ORIGINI, separate da virgola) e risponde al controllo
  "Private Network Access" di Chrome. Senza intestazione Origin ammessa la richiesta viene rifiutata.
- Modello: GUARDIAN_VOCE_MODELLO (cartella con encoder/decoder/joiner/tokens), di default quello già scaricato
  per la plancia locale in ~/.claude/guardian/modelli/.
"""
from __future__ import annotations

import io
import json
import os
import sys
import threading
import wave
from array import array
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

PORTA = int(os.environ.get("GUARDIAN_VOCE_PORTA", "8765"))
MAX_BYTES = 4 * 1024 * 1024
ORIGINI_DEFAULT = "http://localhost:5173,http://localhost:4173,http://127.0.0.1:5173,http://127.0.0.1:4173"
MODELLO_DEFAULT = Path.home() / ".claude" / "guardian" / "modelli" / "sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"

Riconoscitore = Callable[[list[float], int], str]


def leggi_wav(dati: bytes) -> tuple[list[float], int]:
    """WAV PCM 16 bit mono → campioni float in [-1, 1] e frequenza."""
    with wave.open(io.BytesIO(dati)) as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            raise ValueError("serve un WAV mono a 16 bit")
        sr, frame = w.getframerate(), w.readframes(w.getnframes())
    campioni = array("h", frame)
    if sys.byteorder == "big":
        campioni.byteswap()
    return [c / 32768.0 for c in campioni], sr


def sherpa(modello: Path = MODELLO_DEFAULT) -> tuple[Riconoscitore | None, str]:
    """Riconoscitore sherpa-onnx (Parakeet, transducer NeMo). (None, motivo) se non disponibile."""
    try:
        import sherpa_onnx  # noqa: PLC0415
    except ImportError:
        return None, "sherpa-onnx non installato (pip install sherpa-onnx)"
    trova = lambda pref: next((str(p) for p in sorted(modello.glob(f"{pref}*.onnx"))), "")  # noqa: E731
    enc, dec, joi, tok = trova("encoder"), trova("decoder"), trova("joiner"), modello / "tokens.txt"
    if not (enc and dec and joi and tok.exists()):
        return None, f"modello non trovato in {modello}"
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=enc, decoder=dec, joiner=joi, tokens=str(tok),
                                                       model_type="nemo_transducer", num_threads=2)
    lock = threading.Lock()

    def riconosci(campioni: list[float], sr: int) -> str:
        with lock:
            s = rec.create_stream()
            s.accept_waveform(sr, campioni)
            rec.decode_stream(s)
            return s.result.text.strip()
    return riconosci, "sherpa-onnx + Parakeet (locale)"


def crea_server(riconosci: Riconoscitore | None, motivo: str, porta: int = PORTA, origini: set[str] | None = None) -> ThreadingHTTPServer:
    origini = origini or {o.strip() for o in os.environ.get("GUARDIAN_HQ_ORIGINI", ORIGINI_DEFAULT).split(",") if o.strip()}

    class Gestore(BaseHTTPRequestHandler):
        server_version = "GuardianVoce/1"

        def log_message(self, *a):  # niente audio né testo nei log
            pass

        def _origine_ok(self) -> bool:
            return self.headers.get("Origin", "") in origini

        def _intestazioni(self):
            self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin", ""))
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            if self.headers.get("Access-Control-Request-Private-Network") == "true":
                self.send_header("Access-Control-Allow-Private-Network", "true")

        def _json(self, codice: int, dati: dict):
            corpo = json.dumps(dati).encode()
            self.send_response(codice)
            if self._origine_ok():
                self._intestazioni()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_OPTIONS(self):
            if not self._origine_ok():
                self.send_response(403); self.end_headers(); return
            self.send_response(204); self._intestazioni(); self.end_headers()

        def do_GET(self):
            if not self._origine_ok():
                return self._json(403, {"errore": "origine non ammessa"})
            if self.path != "/stato":
                return self._json(404, {"errore": "sconosciuto"})
            self._json(200, {"pronto": riconosci is not None, "motore": motivo, "privato": True})

        def do_POST(self):
            if not self._origine_ok():
                return self._json(403, {"errore": "origine non ammessa"})
            if self.path != "/trascrivi" or riconosci is None:
                return self._json(503 if riconosci is None else 404, {"errore": motivo if riconosci is None else "sconosciuto"})
            n = int(self.headers.get("Content-Length") or 0)
            if not 44 < n <= MAX_BYTES:
                return self._json(413, {"errore": "audio vuoto o troppo lungo"})
            try:
                campioni, sr = leggi_wav(self.rfile.read(n))
                return self._json(200, {"testo": riconosci(campioni, sr)})
            except (ValueError, wave.Error, EOFError) as e:
                return self._json(400, {"errore": str(e)})

    return ThreadingHTTPServer(("127.0.0.1", porta), Gestore)


def main() -> int:
    riconosci, motivo = sherpa(Path(os.environ.get("GUARDIAN_VOCE_MODELLO", MODELLO_DEFAULT)))
    srv = crea_server(riconosci, motivo)
    print(f"Voce locale di Guardian su http://127.0.0.1:{srv.server_address[1]} · {motivo}")
    if riconosci is None:
        print("Il servizio risponde ma non può trascrivere finché il motore non è pronto.", file=sys.stderr)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("Voce locale fermata.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
