#!/bin/bash
# usage: fuzz.sh N SEED [binary-dir]
set -euo pipefail
R="/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)/_reports/gleaner-gitignore-match-repair"
BIN="${3:-/tmp/gl-target/release}"
docker run --rm -v "$R":/r:ro -v "$BIN":/bin-gl:ro gleaner-dev python3 /r/fuzz.py /bin-gl/gleaner "$1" "$2"
