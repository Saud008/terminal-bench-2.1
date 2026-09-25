#!/usr/bin/env bash
set -euo pipefail

ROOT="/app/fixtures/oci-stacks"
WORK="/tmp/oci-layergen"
rm -rf "$WORK"
mkdir -p "$WORK"

build_tar() {
  local name="$1"
  local src="$2"
  tar -cf "$ROOT/$name" -C "$src" .
}

# layer 0
L0="$WORK/l0"
mkdir -p "$L0/etc/app" "$L0/var/log" "$L0/opt/share" "$L0/opt/cache/sub"
printf 'layer0-config' | install -o 1000 -g 1000 -m 0644 /dev/stdin "$L0/etc/app/config.txt"
printf 'log-v0' | install -o 0 -g 0 -m 0644 /dev/stdin "$L0/var/log/app.log"
printf 'share' | install -o 0 -g 0 -m 0644 /dev/stdin "$L0/opt/share/readme.txt"
printf 'cache-hidden' | install -o 0 -g 0 -m 0644 /dev/stdin "$L0/opt/cache/hidden.txt"
printf 'old-sub' | install -o 0 -g 0 -m 0644 /dev/stdin "$L0/opt/cache/sub/old.txt"
build_tar layer0.tar "$L0"

# layer 1
L1="$WORK/l1"
mkdir -p "$L1/etc/app" "$L1/var/log" "$L1/opt/cache/sub"
printf 'layer1-config' | install -o 2000 -g 2000 -m 0644 /dev/stdin "$L1/etc/app/config.txt"
: >"$L1/var/log/.wh.app.log"
printf 'new-sub' | install -o 0 -g 0 -m 0644 /dev/stdin "$L1/opt/cache/sub/new.txt"
build_tar layer1.tar "$L1"

# layer 2
L2="$WORK/l2"
mkdir -p "$L2/opt/cache"
: >"$L2/opt/cache/.wh..wh..opq"
printf 'fresh' | install -o 3000 -g 3000 -m 0644 /dev/stdin "$L2/opt/cache/fresh.txt"
build_tar layer2.tar "$L2"
