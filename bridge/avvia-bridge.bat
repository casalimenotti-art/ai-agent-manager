@echo off
REM Avvia il Guardian Bridge (PC + agenti). Configurazione in bridge\.env (vedi bridge\.env.example).
cd /d "%~dp0.."
python bridge\guardian_bridge.py run %*
