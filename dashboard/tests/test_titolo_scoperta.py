import plancia


def test_skill():
    assert plancia.titolo_scoperta({"nome": "autonnel/autonnel-skills@landing-page-conversion-audit"}) == (
        "Landing page conversion audit", "autonnel/autonnel-skills")


def test_repo():
    assert plancia.titolo_scoperta({"nome": "owner/repo"}) == ("repo", "owner")


def test_semplice_e_vuoto():
    assert plancia.titolo_scoperta({"nome": "skill-demo"}) == ("skill-demo", "")
    assert plancia.titolo_scoperta({}) == ("?", "")
