#!/bin/bash
cd "$(dirname "$0")" || exit 1
ROOT="$PWD"
NODE="$(command -v node)"
if [ -z "$NODE" ]; then
    NODE="/Users/ri/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
fi
if [ ! -x "$NODE" ] || [ ! -x "$ROOT/.venv/bin/python" ]; then
    echo "Не найдено окружение Python или Node.js."
    read -r -p "Нажмите Enter для выхода."
    exit 1
fi
BPID=""
FPID=""
stop() {
    [ -n "$BPID" ] && kill "$BPID" 2>/dev/null
    [ -n "$FPID" ] && kill "$FPID" 2>/dev/null
    return 0
}
trap stop EXIT
trap 'exit 0' INT TERM
if ! lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
    (cd "$ROOT" && exec "$ROOT/.venv/bin/python" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000) &
    BPID=$!
fi
if ! lsof -nP -iTCP:3000 -sTCP:LISTEN >/dev/null 2>&1; then
    (cd "$ROOT/frontend" && export PATH="$(dirname "$NODE"):$PATH" HOST=localhost PORT=3000 BROWSER=none CHOKIDAR_USEPOLLING=true WATCHPACK_POLLING=true && exec "$NODE" node_modules/react-scripts/bin/react-scripts.js start) &
    FPID=$!
fi
echo "Сайт: http://localhost:3000"
echo "API: http://localhost:8000/docs"
echo "Оставьте это окно открытым. Для остановки нажмите Ctrl+C."
open "http://localhost:3000"
if [ -n "$BPID" ] || [ -n "$FPID" ]; then
    wait
fi
