import json, re
import subprocess, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
import skill


@pytest.mark.parametrize("url", [
    "https://github.com/anthropics/skills", "https://github.com/anthropics/skills.git",
    "https://github.com/a/b/", "  https://github.com/a/b-c_d.e  ",
])
def test_url_validi(url):
    assert skill.valida_url(url)


@pytest.mark.parametrize("url", [
    "http://github.com/a/b", "git@github.com:a/b.git", "https://gitlab.com/a/b",
    "https://github.com.evil.com/a/b", "https://evil.com/https://github.com/a/b",
    "https://user@github.com/a/b", "https://github.com/a/b/tree/main", "https://github.com/a",
    "https://github.com/a/..", "https://github.com/a/b?x=1", "file:///etc/passwd",
    "https://github.com/a/b;rm -rf", "", "--upload-pack=x",
])
def test_url_rifiutati(url):
    assert skill.valida_url(url) is None


def test_elenco_e_frontmatter(tmp_path):
    d = tmp_path / "mia"; d.mkdir()
    (d / "SKILL.md").write_text("---\nname: mia-skill\ndescription: >\n  Fa cose\n  utili.\n---\ncorpo")
    (tmp_path / "senza").mkdir(); (tmp_path / "senza" / "SKILL.md").write_text("niente frontmatter")
    r = {s["cartella"]: s for s in skill.elenca_skill(tmp_path)}
    assert r["mia"]["nome"] == "mia-skill" and r["mia"]["descrizione"] == "Fa cose utili."
    assert r["senza"]["nome"] == "senza"


def test_prompt():
    assert skill.prompt_skill("x", " fai y ") == "Usa la skill x per: fai y"


def _repo_locale(tmp_path, con_skill):
    r = tmp_path / "origine"; r.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    if con_skill:
        (r / "SKILL.md").write_text("---\nname: demo\ndescription: d\n---\n")
    else:
        (r / "README").write_text("x")
    subprocess.run(["git", "-C", str(r), "add", "."], check=True)
    subprocess.run(["git", "-C", str(r), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "i"], check=True)
    return r


def test_installa_rifiuta_url_non_github(tmp_path):
    r = skill.installa_locale("https://example.com/a/b", tmp_path)
    assert not r["ok"] and not list(tmp_path.iterdir())


def test_installa_non_sovrascrive(tmp_path):
    (tmp_path / "b").mkdir()
    assert "non la sovrascrivo" in skill.installa_locale("https://github.com/a/b", tmp_path)["messaggio"]


def test_installa_ok_e_senza_skillmd(tmp_path, monkeypatch):
    """Il clone vero è reindirizzato a un repo locale (nessuna rete nei test)."""
    orig_run = subprocess.run
    for con, atteso in ((True, True), (False, False)):
        origine = _repo_locale(tmp_path / ("c" if con else "n"), con)
        base = tmp_path / ("dest_c" if con else "dest_n")

        def finto(cmd, **kw):
            cmd = [str(origine) if str(c).startswith("https://github.com/") else c for c in cmd]
            return orig_run(cmd, **kw)
        monkeypatch.setattr(skill.subprocess, "run", finto)
        r = skill.installa_locale("https://github.com/o/repo", base)
        assert r["ok"] is atteso, r
        assert (base / "repo" / "SKILL.md").exists() is atteso
        assert not (base / "repo" / ".git").exists()
        assert [p.name for p in base.iterdir()] == (["repo"] if atteso else [])  # niente temporanei


def _repo_con_sottocartella(tmp_path, scrivi_skill=True, symlink=False):
    r = tmp_path / "origine"; r.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    d = r / "skills" / "frontend-design"; d.mkdir(parents=True)
    if scrivi_skill:
        (d / "SKILL.md").write_text("---\nname: frontend-design\ndescription: d\n---\n")
    (d / "altro.txt").write_text("x")
    if symlink:
        (d / "x").symlink_to("/etc/passwd")
    subprocess.run(["git", "-C", str(r), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(r), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "i"], check=True)
    return r


def _patch_clone(monkeypatch, origine):
    orig = subprocess.run
    def finto(cmd, **kw):
        cmd = [str(origine) if str(c).startswith("https://github.com/") else c for c in cmd]
        return orig(cmd, **kw)
    monkeypatch.setattr(skill.subprocess, "run", finto)


def test_catalogo_voci_sicure():
    ids = [c["id"] for c in skill.CATALOGO]
    assert len(ids) == len(set(ids)) >= 5
    for c in skill.CATALOGO:
        assert re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+", c["repo"]) and ".." not in c["path"] and not c["path"].startswith("/")


def test_catalogo_id_sconosciuto(tmp_path):
    assert not skill.installa_catalogo_locale("../../etc", tmp_path)["ok"]
    assert not list(tmp_path.iterdir())


def test_installa_catalogo_ok(tmp_path, monkeypatch):
    _patch_clone(monkeypatch, _repo_con_sottocartella(tmp_path))
    base = tmp_path / "skills"
    r = skill.installa_catalogo_locale("frontend-design", base)
    assert r["ok"], r
    assert (base / "frontend-design" / "SKILL.md").is_file()
    assert json.loads((base / "frontend-design" / ".guardian-source.json").read_text())["commit"]
    assert next(c for c in skill.catalogo_locale(base) if c["id"] == "frontend-design")["installata"]
    assert "già installata" in skill.installa_catalogo_locale("frontend-design", base)["messaggio"]  # no overwrite


def test_installa_catalogo_rifiuta_symlink_e_senza_skillmd(tmp_path, monkeypatch):
    _patch_clone(monkeypatch, _repo_con_sottocartella(tmp_path / "a", symlink=True))
    base = tmp_path / "skills"
    assert "simbolici" in skill.installa_catalogo_locale("frontend-design", base)["messaggio"]
    assert not (base / "frontend-design").exists()
    _patch_clone(monkeypatch, _repo_con_sottocartella(tmp_path / "b", scrivi_skill=False))
    assert not skill.installa_catalogo_locale("frontend-design", base)["ok"]


def test_elenca_skill_tutte_le_origini(tmp_path, monkeypatch):
    import config
    home = tmp_path / "home"
    def sk(p, nome):
        (home / p).mkdir(parents=True); (home / p / "SKILL.md").write_text(f"---\nname: {nome}\ndescription: d {nome}\n---\n")
    sk("skills/mia", "mia")
    sk("skills/synced/uuid/docx", "docx")
    sk("skills/synced/uuid/mia", "mia")                      # duplicato per nome: vince "installata"
    sk("plugins/synced/a/b/skills/brainstorming", "brainstorming")
    monkeypatch.setattr(config, "CLAUDE_HOME", home)
    r = {s["nome"]: s["origine"] for s in skill.elenca_skill()}
    assert r == {"mia": "installata", "docx": "account", "brainstorming": "plugin"}


def test_graphify_comandi_sicuri_e_nessuna_sovrascrittura(tmp_path, monkeypatch):
    import config, types
    monkeypatch.setattr(config, "CLAUDE_HOME", tmp_path / "h")
    monkeypatch.setattr(config, "EVENTS_FILE", tmp_path / "g" / "e.jsonl")
    (tmp_path / "h").mkdir(); (tmp_path / "h" / "CLAUDE.md").write_text("mie istruzioni")
    base = tmp_path / "h" / "skills"
    chiamate = []
    def finto(cmd, **kw):
        chiamate.append(cmd)
        if "install" in cmd and "--platform" in cmd:
            (base / "graphify").mkdir(parents=True); (base / "graphify" / "SKILL.md").write_text("x")
        return types.SimpleNamespace(returncode=0, stderr="", stdout="")
    r = skill.installa_graphify_locale(base, tmp_path / "venv", runner=finto)
    assert r["ok"], r
    pip = next(c for c in chiamate if "pip" in c)
    assert "--only-binary=:all:" in pip and "graphifyy==0.9.120" in pip       # versione fissata, nome corretto, solo wheel
    assert not any("graphify" in c and "hook" in " ".join(c) for c in chiamate)  # nessun hook
    assert not any("--break-system-packages" in c for c in chiamate)
    assert (tmp_path / "h" / "CLAUDE.md.guardian-bak").read_text() == "mie istruzioni"
    assert "già installata" in skill.installa_graphify_locale(base, tmp_path / "venv", runner=finto)["messaggio"]


def test_graphify_errore_pip_non_crea_nulla(tmp_path, monkeypatch):
    import config, types
    monkeypatch.setattr(config, "CLAUDE_HOME", tmp_path / "h")
    monkeypatch.setattr(config, "EVENTS_FILE", tmp_path / "g" / "e.jsonl")
    finto = lambda cmd, **kw: types.SimpleNamespace(returncode=1, stderr="boom", stdout="")
    r = skill.installa_graphify_locale(tmp_path / "h" / "skills", tmp_path / "venv", runner=finto)
    assert not r["ok"] and "boom" in r["messaggio"] and not (tmp_path / "h" / "skills").exists()


def test_catalogo_graphify_dispatch(tmp_path, monkeypatch):
    monkeypatch.setattr(skill, "installa_graphify_locale", lambda b=None: {"ok": True, "messaggio": "ok"})
    assert skill.installa_catalogo_locale("graphify", tmp_path)["ok"]
