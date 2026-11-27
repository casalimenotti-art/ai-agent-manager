import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

RADICE = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE / "dashboard"))
sys.path.insert(0, str(RADICE / "registro"))
import accesso  # noqa: E402
import scrivi  # noqa: E402
import team  # noqa: E402

ORA = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)


def _voce(chi, azione, ts="2026-11-27T10:00:00+00:00", esito="fatto"):
    return json.dumps({"ts": ts, "chi": chi, "agente": "codex", "azione": azione, "file": ["a.csv"], "esito": esito})


def test_analizza_righe_ignora_righe_rotte():
    testo = "\n".join([_voce("amico1", "bozze"), "non json", "{}", json.dumps({"chi": "x"}), "", _voce("menotti", "sito")])
    v = team.analizza_righe(testo, "locale")
    assert [x["chi"] for x in v] == ["amico1", "menotti"]
    assert v[0]["file"] == ["a.csv"] and v[0]["fonte"] == "locale"


def test_riepilogo_per_persona():
    persone = [{"id": "menotti"}, {"id": "amico1"}, {"id": "amico2"}]
    voci = team.analizza_righe("\n".join([
        _voce("amico1", "nuova", "2026-11-27T11:00:00+00:00", "bloccato"),
        _voce("amico1", "vecchia", "2026-11-26T11:00:00+00:00"),
        _voce("menotti", "sito", "2026-11-27T09:00:00+00:00")]))
    voci.sort(key=lambda v: v["ts"], reverse=True)
    r = {p["id"]: p for p in team.riepilogo(persone, voci, ORA)}
    assert r["amico1"]["ultima"]["azione"] == "nuova" and r["amico1"]["oggi"] == 1 and r["amico1"]["bloccate"] == 1
    assert r["menotti"]["oggi"] == 1 and r["amico2"]["ultima"] is None


def test_quando():
    assert team.quando("2026-11-27T11:59:30+00:00", ORA) == "adesso"
    assert team.quando("2026-11-27T11:30:00+00:00", ORA) == "30 min fa"
    assert team.quando("rotto", ORA) == "rotto"


def test_registro_da_cartella_e_da_branch(tmp_path):
    def git(*a):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=tmp_path, check=True, capture_output=True)
    git("init", "-q", "-b", "main")
    (tmp_path / "registro").mkdir()
    (tmp_path / "registro" / "persone.json").write_text('[{"id":"menotti"},{"id":"amico1"}]', encoding="utf-8")
    (tmp_path / "registro" / "menotti.jsonl").write_text(_voce("menotti", "sito") + "\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "inizio")
    git("checkout", "-qb", "codex/vendite")
    (tmp_path / "registro" / "amico1.jsonl").write_text(_voce("amico1", "bozze", "2026-11-27T11:00:00+00:00") + "\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "bozze")
    git("checkout", "-q", "main")   # amico1.jsonl NON è nella cartella di lavoro di main
    assert not (tmp_path / "registro" / "amico1.jsonl").exists()
    voci = team.leggi_registro(tmp_path)
    assert [v["azione"] for v in voci] == ["bozze", "sito"]   # niente doppioni, dalla più recente
    assert [p["id"] for p in team.leggi_persone(tmp_path)] == ["menotti", "amico1"]
    assert {c["messaggio"] for c in team.commit_recenti(tmp_path, giorni=3650)} == {"inizio", "bozze"}


def test_registro_senza_git(tmp_path):
    assert team.leggi_registro(tmp_path) == [] and team.leggi_persone(tmp_path) == []


def test_scrivi_crea_voce_e_blocca_segreti():
    v = scrivi.crea_voce("amico1", "codex", "  Preparate   5 bozze ", ["leads/x.csv"], "fatto", "codex/vendite", ORA)
    assert v == {"ts": "2026-11-27T12:00:00+00:00", "chi": "amico1", "agente": "codex", "azione": "Preparate 5 bozze",
                 "file": ["leads/x.csv"], "esito": "fatto", "branch": "codex/vendite"}
    for brutto in ("chiave sk-abcdefghijklmnopqrstuv", "password: ciao123", "token=abc"):
        try:
            scrivi.crea_voce("amico1", "codex", brutto)
            assert False, brutto
        except ValueError:
            pass
    for vuoto in ("", "   "):
        try:
            scrivi.crea_voce("amico1", "codex", vuoto)
            assert False
        except ValueError:
            pass


def test_ruolo_pin_titolare_e_ospite():
    ht, ho = accesso.crea_hash("111111"), accesso.crea_hash("222222")
    assert accesso.ruolo_pin("111111", ht, ho) == "titolare"
    assert accesso.ruolo_pin("222222", ht, ho) == "ospite"
    assert accesso.ruolo_pin("333333", ht, ho) is None
    assert accesso.ruolo_pin("222222", "", ho) == "ospite"
    assert accesso.ruolo_pin("111111", ht, "") == "titolare"


import passa  # noqa: E402


def test_passaggio_testo_e_stati():
    t = passa.testo_passaggio("menotti", "claude-code", "chiunque", "Rifare la galleria", "metà fatta", "finire i test",
                              ["dashboard/app.py"], "claude/dashboard-pc", "2026-11-27T03:00:00+00:00")
    assert passa.stato(t) == "aperto" and "## Prossimi passi\nfinire i test" in t
    t2 = passa.cambia_stato(t, "preso", "amico1", "2026-11-27T04:00:00+00:00")
    assert passa.stato(t2) == "preso" and "preso da amico1" in t2
    assert passa.stato(passa.cambia_stato(t2, "chiuso", "amico1", "x")) == "chiuso"


def test_passaggi_aperti_stato_piu_avanzato_vince(tmp_path):
    def git(*a):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=tmp_path, check=True, capture_output=True)
    t = passa.testo_passaggio("menotti", "claude-code", "chiunque", "Galleria", "", "", [], "b", "2026-11-27T03:00:00+00:00")
    git("init", "-q", "-b", "main")
    (tmp_path / "passaggi").mkdir()
    (tmp_path / "passaggi" / "p1.md").write_text(t, encoding="utf-8")
    (tmp_path / "passaggi" / "p2.md").write_text(t.replace("Galleria", "Voce"), encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "apri")
    assert {p["titolo"] for p in team.passaggi_aperti(tmp_path)} == {"Galleria", "Voce"}
    git("checkout", "-qb", "codex/vendite")   # l'amico chiude p1 sul suo branch
    (tmp_path / "passaggi" / "p1.md").write_text(passa.cambia_stato(t, "chiuso", "amico1", "x"), encoding="utf-8")
    git("commit", "-qam", "chiudi")
    git("checkout", "-q", "main")             # in locale p1 risulta ancora aperto
    assert [p["titolo"] for p in team.passaggi_aperti(tmp_path)] == ["Voce"]


def test_hook_passaggio_soglia():
    sys.path.insert(0, str(RADICE / "dashboard" / "hooks"))
    import guardian_passaggio as gp
    ora = 1000.0
    assert gp.messaggio({"five_hour": {"pct": 95}, "ts": ora}, 90, ora).startswith("ATTENZIONE: utilizzo Claude al 95%")
    assert gp.messaggio({"five_hour": {"pct": 50}, "seven_day": {"pct": 91}, "ts": ora}, 90, ora) is not None
    assert gp.messaggio({"five_hour": {"pct": 89}, "ts": ora}, 90, ora) is None
    assert gp.messaggio({"five_hour": {"pct": 99}, "ts": 0}, 90, ora) is None   # dati vecchi
    assert gp.messaggio({}, 90, ora) is None


def test_registro_condiviso_aggiorna_due_checkout_dopo_push(tmp_path):
    import threading

    def git(repo, *args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.test", *args],
                       cwd=repo, check=True, capture_output=True)

    git(tmp_path, "init", "--bare", "-b", "main", "origin.git")
    git(tmp_path, "clone", "origin.git", "autore")
    autore = tmp_path / "autore"
    cartella = autore / "registro"
    cartella.mkdir()
    (cartella / "persone.json").write_text('[{"id":"menotti"},{"id":"amico2"}]', encoding="utf-8")
    (cartella / "menotti.jsonl").write_text(_voce("menotti", "Avviato Guardian") + "\n", encoding="utf-8")
    git(autore, "add", "registro")
    git(autore, "commit", "-m", "Inizio")
    git(autore, "push", "origin", "main")
    lettori = []
    for nome in ("nicola", "menotti"):
        git(tmp_path, "clone", "origin.git", nome)
        lettori.append(team.RegistroCondiviso(tmp_path / nome, intervallo=0))

    def sync(lettore):
        pronto = threading.Event()
        aggiorna = lettore._aggiorna

        def lavoro():
            try:
                aggiorna()
            finally:
                pronto.set()

        lettore._aggiorna = lavoro
        lettore.leggi()
        assert pronto.wait(8)
        lettore._aggiorna = aggiorna
        return lettore._stato

    for lettore in lettori:
        stato = sync(lettore)
        assert stato.aggiornato and not stato.errore
        assert [v["azione"] for v in stato.voci] == ["Avviato Guardian"]

    git(autore, "switch", "-c", "codex/amministrazione")
    (cartella / "amico2.jsonl").write_text(_voce("amico2", "Competenza verificata") + "\n", encoding="utf-8")
    git(autore, "add", "registro/amico2.jsonl")
    git(autore, "commit", "-m", "Registra il lavoro")
    git(autore, "push", "origin", "codex/amministrazione")
    (tmp_path / "nicola" / "registro" / "amico2.jsonl").write_text(_voce("amico2", "Bozza privata"), encoding="utf-8")
    for lettore in lettori:
        stato = sync(lettore)
        assert {v["azione"] for v in stato.voci} == {"Avviato Guardian", "Competenza verificata"}
        assert any(v["fonte"] == "origin/codex/amministrazione" for v in stato.voci)


def test_link_passaggio_codifica_il_nome_e_rimane_su_github():
    assert "/blob/codex/dashboard/passaggi/registro%20nuovo.md" in team.link_passaggio("codex/dashboard", "registro nuovo.md")
    assert team.link_passaggio("main", "../estraneo.md") == ""
