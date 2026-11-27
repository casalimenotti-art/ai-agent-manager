#!/usr/bin/env bash
# Prova le migrazioni Supabase su un PostgreSQL locale usa-e-getta (serve postgresql installato; da root usa l'utente postgres).
# Uso: bash tests/pg/run.sh
set -euo pipefail
QUI="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$QUI/../.." && pwd)"
PGBIN="$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1)"
[ -x "$PGBIN/initdb" ] || { echo "PostgreSQL non installato: test saltato"; exit 0; }
D="$(mktemp -d /var/tmp/guardian-pg.XXXX)"; chmod 777 "$D"
COME=(); [ "$(id -u)" = 0 ] && COME=(su postgres -c)
esegui() { if [ ${#COME[@]} -gt 0 ]; then "${COME[@]}" "$1"; else bash -c "$1"; fi; }
esegui "$PGBIN/initdb -D $D/data -A trust -U postgres >/dev/null"
esegui "$PGBIN/pg_ctl -D $D/data -o '-k $D -p 55433 -c listen_addresses=' -l $D/log start >/dev/null"
trap 'esegui "$PGBIN/pg_ctl -D $D/data stop -m fast >/dev/null"; rm -rf "$D"' EXIT
P=(psql -h "$D" -p 55433 -U postgres -v ON_ERROR_STOP=1 -q -X)
"${P[@]}" -c "create database g"
"${P[@]}" -d g -f "$QUI/shim.sql" 2>/dev/null
"${P[@]}" -d g -f "$REPO/supabase/migrations/001_guardian.sql" 2>&1 | sed "/NOTICE/d"
"${P[@]}" -d g -f "$QUI/dati_v1.sql"
for i in 1 2; do "${P[@]}" -d g -f "$REPO/supabase/migrations/002_command_center.sql" 2>&1 | sed -E "/NOTICE|already exists|does not exist/d"; done
"${P[@]}" -d g -t -A -f "$QUI/check_002.sql"
