#!/bin/bash
# usage: fuzzmany.sh N SEED1 SEED2 ... (builds first)
set -uo pipefail
D="/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)/_reports/gleaner-gitignore-match-repair"
bash "$D/build.sh" | tail -2
n=$1; shift
for s in "$@"; do bash "$D/fuzz.sh" "$n" "$s" > /tmp/fz-$s.log 2>&1 & done
wait
for s in "$@"; do tail -1 /tmp/fz-$s.log; done
for s in "$@"; do if ! tail -1 /tmp/fz-$s.log | grep -q ' 0 mismatching'; then tail -60 /tmp/fz-$s.log; break; fi; done
