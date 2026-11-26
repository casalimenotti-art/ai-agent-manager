@echo off
rem Avvio Guardian con doppio clic su Windows: crea l'ambiente al primo giro, installa, apre il browser.
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" goto :pronto
echo Primo avvio: preparo l'ambiente, ci vogliono 1-2 minuti...
py -3 -m venv .venv
if errorlevel 1 python -m venv .venv
if errorlevel 1 goto :errore
:pronto
call ".venv\Scripts\activate.bat"
pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :errore
start "" "http://localhost:8501"
streamlit run app.py --server.address localhost --server.port 8501 --server.headless true
goto :fine
:errore
echo.
echo ERRORE: serve Python 3.11 o superiore. Installalo da python.org e riprova.
:fine
pause
