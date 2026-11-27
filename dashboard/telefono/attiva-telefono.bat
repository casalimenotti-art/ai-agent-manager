@echo off
set "TS="
where tailscale >nul 2>nul && set "TS=tailscale"
if not defined TS if exist "C:\Program Files\Tailscale\tailscale.exe" set "TS=C:\Program Files\Tailscale\tailscale.exe"
if not defined TS (
  echo Tailscale non e' installato. Scaricalo da https://tailscale.com/download e accedi con lo stesso account sul PC e sul telefono.
  pause
  exit /b 1
)
findstr /b /c:"GUARDIAN_PIN_HASH=" "%~dp0..\.env" >nul 2>nul
if errorlevel 1 (
  echo PIN non impostato. Esegui prima imposta-pin.bat, poi rilancia questo file.
  pause
  exit /b 1
)
"%TS%" serve --bg 8501
"%TS%" serve status
echo.
echo Apri sul telefono l'indirizzo https://... mostrato sopra
pause
