"""Comandi locali e visuale dell’avatar Guardian."""
import re

from plancia import normalizza_voce
from theme import esc

_STATI = {"riposo": "Pronto", "ascolto": "In ascolto", "pensiero": "Elaborazione",
          "felice": "Risposta pronta", "errore": "Richiesta non riuscita"}
_GESTI = {"saluta": "saluta", "annuisci": "annuisci", "vieni al centro": "centro"}


def comando_da_testo(testo: str) -> dict | None:
    frase = normalizza_voce(testo).removeprefix("guardian ")
    if direzione := re.fullmatch(r"guarda (?:a )?(destra|sinistra|su|giu)", frase):
        return {"azione": "guarda", "dir": direzione[1]}
    if frase in _GESTI:
        return {"azione": _GESTI[frase]}
    return None


def visuale(stato: str, comando: dict | None = None) -> str:
    stato = stato if stato in _STATI else "riposo"
    comando = comando or {}
    movimento = comando.get("dir", comando.get("azione", "centro"))
    if movimento not in {"destra", "sinistra", "su", "giu", "saluta", "annuisci", "centro"}:
        movimento = "centro"
    return f"""<div class="guardian-avatar {stato}" data-movimento="{movimento}">
      <div class="guardian-holo" aria-hidden="true">
        <div class="guardian-orbit"></div><div class="guardian-face">
          <div class="guardian-eyes"><i></i><i></i></div><div class="guardian-mouth"></div>
        </div>
      </div>
      <strong>Guardian</strong><span>{esc(_STATI[stato])}</span><span class="guardian-speaking">Sta parlando</span>
    </div>"""
