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
