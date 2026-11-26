#!/usr/bin/env bash
# Avvio Guardian con un comando solo (macOS/Linux): crea l'ambiente al primo giro, installa, apre il browser.
set -e
cd "$(dirname "$0")"
PORTA="${GUARDIAN_PORT:-8501}"
if [ ! -d .venv ]; then
  echo "Primo avvio: preparo l'ambiente (1-2 minuti)..."
  python3 -m venv .venv
fi
. .venv/bin/activate
pip install -q --disable-pip-version-check -r requirements.txt
( sleep 3; (command -v open >/dev/null && open "http://localhost:$PORTA") || (command -v xdg-open >/dev/null && xdg-open "http://localhost:$PORTA") || true ) &
exec streamlit run app.py --server.address localhost --server.port "$PORTA" --server.headless true
