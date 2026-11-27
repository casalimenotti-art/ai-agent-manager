@echo off
rem PIN per gli amici: vedono la dashboard in sola lettura (niente chat con Guardian, niente lanci di agenti).
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (".venv\Scripts\python.exe" telefono\imposta_pin.py --ospiti) else (python telefono\imposta_pin.py --ospiti)
pause
