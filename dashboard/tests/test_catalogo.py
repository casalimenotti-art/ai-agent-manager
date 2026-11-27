import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import catalogo


def test_frontmatter_semplice_e_piegato(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("---\nname: web-designer\ndescription: >\n  Disegna siti: belli\n  e veloci\ntools: Read, Edit, Bash\n---\nCorpo", encoding="utf-8")
    m = catalogo.leggi_frontmatter(f)
    assert m["name"] == "web-designer"
    assert m["description"] == "Disegna siti: belli e veloci"
    assert m["tools"] == ["Read", "Edit", "Bash"]


def test_file_mancante_o_malformato(tmp_path):
    assert catalogo.leggi_frontmatter(tmp_path / "no.md") == {}
    g = tmp_path / "b.md"
    g.write_text("niente frontmatter", encoding="utf-8")
    assert catalogo.leggi_frontmatter(g) == {}
    g.write_bytes(b"---\n\xff\xfe: ::\n  rotto\n---")
    assert isinstance(catalogo.leggi_frontmatter(g), dict)
    assert catalogo.scheda_agente("inesistente", tmp_path)["esiste"] is False


def test_scheda_agente(tmp_path):
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "x.md").write_text("---\nname: x\ndescription: Fa cose\ntools: [Read, Grep]\n---\n", encoding="utf-8")
    s = catalogo.scheda_agente("x", tmp_path)
    assert s["descrizione"] == "Fa cose" and s["tools"] == ["Read", "Grep"] and s["esiste"]


def test_filtro_ricerca():
    voci = [{"nome": "web-designer", "ruolo": "Web designer"}, {"nome": "ricercatore-web", "ruolo": "Ricercatore web"},
            {"nome": "pdf", "descrizione": "Legge documenti"}]
    assert len(catalogo.filtra(voci, "")) == 3
    assert [v["nome"] for v in catalogo.filtra(voci, "RICERC")] == ["ricercatore-web"]
    assert [v["nome"] for v in catalogo.filtra(voci, "web designer")] == ["web-designer"]
    assert [v["nome"] for v in catalogo.filtra(voci, "documenti")] == ["pdf"]
    assert catalogo.filtra(voci, "zzz") == []


def test_percorso_skill_sicuro(tmp_path):
    assert catalogo.percorso_skill("../x", tmp_path) is None
    (tmp_path / "skills" / "pdf").mkdir(parents=True)
    (tmp_path / "skills" / "pdf" / "SKILL.md").write_text("x", encoding="utf-8")
    assert catalogo.percorso_skill("pdf", tmp_path).name == "SKILL.md"


def test_categorie_agenti():
    assert catalogo.categoria_agente("web-designer") == "Sviluppo"
    assert catalogo.categoria_agente("sviluppatore-dashboard") == "Sviluppo"
    assert catalogo.categoria_agente("cacciatore-clienti") == "Squadra"
    assert catalogo.categoria_agente("ricercatore-web") == "Squadra"
    assert catalogo.categoria_agente("scout-strumenti") == "Squadra"
    assert catalogo.categoria_agente("forgiatore-agenti") == "Sistema"


def test_skill_it_mappa_e_fallback(tmp_path):
    m = catalogo.carica_mappa_it()
    assert len(m) >= 50 and all(len(v) <= 110 for v in m.values())
    assert catalogo.descrizione_it("pdf", "orig", m) == m["pdf"]
    assert catalogo.descrizione_it("sconosciuta", "orig", m) == "orig"
    assert catalogo.descrizione_it("x", "orig", None) == "orig"


def test_skill_it_file_rotto_o_mancante(tmp_path):
    rotto = tmp_path / "r.json"
    rotto.write_text("{non json", encoding="utf-8")
    assert catalogo.carica_mappa_it(rotto) == {}
    assert catalogo.carica_mappa_it(tmp_path / "manca.json") == {}


def test_skill_it_copre_le_skill_elencate():
    import fonte
    nomi = [s["nome"] for s in fonte.FonteLocale().skill_elenco()]
    m = catalogo.carica_mappa_it()
    assert [n for n in nomi if n not in m] == []
