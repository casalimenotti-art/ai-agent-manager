import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import monitor


def test_riconosce_nome_claude():
    assert monitor.e_processo_claude("claude", [])


def test_riconosce_percorso_npm():
    cmd = ["node", "/usr/lib/node_modules/@anthropic-ai/claude-code/cli.js", "-p"]
    assert monitor.e_processo_claude("node", cmd)


def test_ignora_bash_che_cita_il_percorso_negli_argomenti_lontani():
    cmd = ["/bin/bash", "-c", "@anthropic-ai/claude-code"]
    assert not monitor.e_processo_claude("bash", cmd)


def test_ignora_altri():
    assert not monitor.e_processo_claude("python", ["python", "x.py"])


def test_cpu_storico_potato():
    c = monitor.Campionatore(storico_s=0.2)
    c.cpu_totale()
    import time; time.sleep(0.3)
    r = c.cpu_totale()
    assert len(r["storico"]) == 1
