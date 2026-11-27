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


def insegui_puntatore() -> str:
    """Segue il puntatore a riposo, senza raccogliere o trasmettere coordinate."""
    return """<script>
    try {
      const page = window.parent.document;
      if (!page.body.dataset.guardianPointer) {
        page.body.dataset.guardianPointer = "1";
        let pending = false;
        page.addEventListener("pointermove", event => {
          if (pending || window.parent.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
          pending = true;
          window.parent.requestAnimationFrame(() => {
            pending = false;
            const face = page.querySelector(".guardian-avatar.riposo[data-movimento=centro] .guardian-eyes");
            if (!face) return;
            const box = face.getBoundingClientRect();
            face.style.setProperty("--ex", Math.max(-6, Math.min(6, (event.clientX - box.x - box.width / 2) / 30)) + "px");
            face.style.setProperty("--ey", Math.max(-4, Math.min(4, (event.clientY - box.y) / 30)) + "px");
          });
        }, {passive: true});
      }
    } catch {}
    </script>"""
