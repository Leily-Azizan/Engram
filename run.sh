#!/usr/bin/env bash
# Start Engram locally.
set -e
cd "$(dirname "$0")"

PY=.venv/bin/python

"$PY" manage.py migrate --noinput
"$PY" manage.py seed_content
echo
echo "Engram is starting at http://127.0.0.1:8000  (Ctrl-C to stop)"
echo
exec "$PY" manage.py runserver "${1:-127.0.0.1:8000}"
