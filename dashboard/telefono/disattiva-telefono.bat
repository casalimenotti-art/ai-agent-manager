@echo off
set "TS=tailscale"
where tailscale >nul 2>nul || set "TS=C:\Program Files\Tailscale\tailscale.exe"
"%TS%" serve reset
echo Accesso dal telefono disattivato.
pause
