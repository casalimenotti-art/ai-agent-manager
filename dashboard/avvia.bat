@echo off
rem Avvio Guardian con doppio clic (Windows): crea l'ambiente al primo giro, installa, apre il browser.
cd /d "%~dp0"
if not exist .venv (
  echo Primo avvio: preparo l'ambiente, ci vogliono 1-2 minuti...
  py -3 -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q --disable-pip-version-check -r requirements.txt
start "" "http://localhost:8501"
streamlit run app.py --server.address localhost --server.port 8501 --server.headless true
pause
