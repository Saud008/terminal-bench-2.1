#!/bin/bash
# usage: fuzz253.sh N SEED... -> fuzz /tmp/gl-target/release/gleaner against WSL git (2.53); also against container git 2.39 for same seeds
set -uo pipefail
D="/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)/_reports/gleaner-gitignore-match-repair"
bash "$D/mkcorrect.sh" | grep -E 'error|warning' || true
cp /tmp/gl-target/release/gleaner /tmp/gleaner-bin
n=$1; shift
for s in "$@"; do (cd /tmp && python3 "$D/fuzz.py" /tmp/gleaner-bin "$n" "$s" | tail -30); done
