#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$ROOT_DIR"

if [ -x "./stop.sh" ]; then
    ./stop.sh || true
fi

sleep 1

exec ./start_with_tunnel.sh
