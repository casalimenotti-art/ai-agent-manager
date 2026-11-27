"""Imposta il PIN di accesso remoto: scrive solo l'impronta in dashboard/.env.

  imposta_pin.py            -> GUARDIAN_PIN_HASH (titolare: accesso completo)
  imposta_pin.py --ospiti   -> GUARDIAN_PIN_OSPITI_HASH (amici: sola lettura, niente chat ne' lanci)
"""
import getpass
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import accesso  # noqa: E402

ENV = BASE / ".env"


def _valore(righe: list[str], chiave: str) -> str:
    for r in righe:
        if r.split("=", 1)[0].strip() == chiave:
            return r.split("=", 1)[1].strip() if "=" in r else ""
    return ""


def main(argv=None) -> int:
    ospiti = "--ospiti" in (sys.argv[1:] if argv is None else argv)
    chiave = "GUARDIAN_PIN_OSPITI_HASH" if ospiti else "GUARDIAN_PIN_HASH"
    altra = "GUARDIAN_PIN_HASH" if ospiti else "GUARDIAN_PIN_OSPITI_HASH"
    print("PIN OSPITI (sola lettura, da dare agli amici)." if ospiti else "PIN TITOLARE (accesso completo, solo per te).")
    p1 = getpass.getpass("Nuovo PIN (minimo 6 caratteri): ")
    if len(p1) < 6:
        print("PIN troppo corto: servono almeno 6 caratteri.")
        return 1
    if getpass.getpass("Ripeti il PIN: ") != p1:
        print("I due PIN non coincidono.")
        return 1
    righe = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    if accesso.verifica_pin(p1, _valore(righe, altra)):
        print("Questo PIN e' gia' usato per l'altro accesso: scegline uno diverso.")
        return 1
    riga = f"{chiave}={accesso.crea_hash(p1)}"
    nuove, fatto = [], False
    for r in righe:
        if r.split("=", 1)[0].strip() == chiave:
            if not fatto:
                nuove.append(riga)
            fatto = True
        else:
            nuove.append(r)
    if not fatto:
        nuove.append(riga)
    ENV.write_text("\n".join(nuove) + "\n", encoding="utf-8")
    print("PIN salvato (in forma cifrata). Riavvia la dashboard per applicarlo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
