#!/bin/sh
set -e

# 简单的 entrypoint，用于转发 SIGTERM/SIGINT 给子进程，支持优雅停机
_term() {
  echo "Caught SIGTERM/SIGINT, forwarding to child..."
  kill -TERM "$child" 2>/dev/null || true
}

trap _term SIGTERM
trap _term SIGINT

# 启动命令并等待
"$@" &
child=$!
wait "$child"
exit $?
