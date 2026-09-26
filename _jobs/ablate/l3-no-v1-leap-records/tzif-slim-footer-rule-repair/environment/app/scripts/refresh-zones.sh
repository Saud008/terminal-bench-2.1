#!/usr/bin/env bash
# Rebuild /app/zones from an IANA tzdata release.
#   scripts/refresh-zones.sh 2025b
set -euo pipefail

release="${1:?tzdata release, e.g. 2025b}"
here="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

curl -fsSL -o "$work/tzdata.tar.gz" "https://data.iana.org/time-zones/releases/tzdata${release}.tar.gz"
tar -xzf "$work/tzdata.tar.gz" -C "$work"

out="$work/out"
(cd "$work" && zic -b slim -d "$out" africa antarctica asia australasia europe northamerica southamerica etcetera backward)

while read -r zone; do
    [ -z "$zone" ] && continue
    mkdir -p "$here/zones/$(dirname "$zone")"
    cp "$out/$zone" "$here/zones/$zone"
done < "$here/zones/SITES"

echo "$release" > "$here/zones/VERSION"
