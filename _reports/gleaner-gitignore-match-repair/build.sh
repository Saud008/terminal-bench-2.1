#!/bin/bash
# usage: build.sh [SRC_APP_DIR] [OUT_DIR]  -> compiles a gleaner app dir (default environment/app) and copies the binary to OUT_DIR
set -euo pipefail
R="/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)"
T="$R/gleaner-gitignore-match-repair/gleaner-gitignore-match-repair"
SRC="${1:-$T/environment/app}"
OUT="${2:-/tmp/gl-target/release}"
if ! docker image inspect gleaner-dev >/dev/null 2>&1; then
  docker build -q -t gleaner-dev -f "$R/_reports/gleaner-gitignore-match-repair/dev.Dockerfile" "$R/_reports/gleaner-gitignore-match-repair"
fi
mkdir -p /tmp/gl-cargo "$OUT"
docker run --rm -v "$SRC":/src:ro -v /tmp/gl-cargo:/tgt -v "$OUT":/out -e CARGO_TARGET_DIR=/tgt gleaner-dev \
  bash -c 'cp -r /src /build && cd /build && cargo build --release --offline --locked 2>&1 | grep -E "^(warning|error)|-->|Finished" | head -60; cp /tgt/release/gleaner /out/gleaner'
ls -la "$OUT/gleaner"
