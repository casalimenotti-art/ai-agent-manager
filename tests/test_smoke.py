from guardian.core.store import seed_users_da_registro
from guardian.core.store_sqlite import SqliteStore
from scripts.smoke_supabase import main, passi_store


def test_smoke_passi_su_sqlite():
    s = SqliteStore(":memory:")
    seed_users_da_registro(s)
    esiti = passi_store(s, "menotti")
    assert all(ok for _, ok, _ in esiti), esiti
    assert s.tasks()[0]["stato"] == "cancelled"


def test_smoke_senza_configurazione_spiega_come_usarlo(monkeypatch, capsys):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    assert main([]) == 2 and "SUPABASE_URL" in capsys.readouterr().out
