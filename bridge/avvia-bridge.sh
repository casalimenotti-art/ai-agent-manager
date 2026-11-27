#!/usr/bin/env bash
# Avvia il Guardian Bridge (PC + agenti). Configurazione in bridge/.env (vedi bridge/.env.example).
cd "$(dirname "$0")/.." && exec python3 bridge/guardian_bridge.py run "$@"
