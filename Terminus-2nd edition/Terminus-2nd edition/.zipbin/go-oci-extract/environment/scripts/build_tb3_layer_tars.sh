#!/usr/bin/env bash
set -euo pipefail

ROOT="/opt/verifier-fixtures/oci-layers"
WORK="/tmp/oci-tb3gen"
rm -rf "$WORK"
mkdir -p "$WORK"

build_tar() {
  local name="$1"
  local src="$2"
  tar -cf "$ROOT/$name" -C "$src" .
}

# tb3 layer 0 — duplicate slash path
L0="$WORK/l0"
mkdir -p "$L0/etc//slash/app" "$L0/var/run"
printf 'slash-app' | install -o 10 -g 10 -m 0644 /dev/stdin "$L0/etc//slash/app/main.txt"
printf 'tb3-keep' | install -o 0 -g 0 -m 0644 /dev/stdin "$L0/var/run/keep.txt"
build_tar tb3-layer0.tar "$L0"

# tb3 layer 1 — metadata override on normalized slash path + whiteout
L1="$WORK/l1"
mkdir -p "$L1/etc/slash/app" "$L1/var/run"
printf 'slash-updated' | install -o 88 -g 88 -m 0644 /dev/stdin "$L1/etc/slash/app/main.txt"
: >"$L1/var/run/.wh.keep.txt"
build_tar tb3-layer1.tar "$L1"
