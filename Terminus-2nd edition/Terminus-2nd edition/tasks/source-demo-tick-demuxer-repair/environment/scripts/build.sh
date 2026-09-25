#!/usr/bin/env bash
set -euo pipefail
make -C /app/src demux-read
install -m 0755 /app/src/demux-read /app/bin/demux-read
