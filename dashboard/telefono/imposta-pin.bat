@echo off
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (".venv\Scripts\python.exe" telefono\imposta_pin.py) else (python telefono\imposta_pin.py)
pause
