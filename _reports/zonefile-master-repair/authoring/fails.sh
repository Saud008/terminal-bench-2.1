#!/usr/bin/env bash
cd ~/tbruns || exit 1
for t in zonefile-master-repair-k2-20260927-052835/*/ zonefile-master-repair-k3-20260927-055035/*/; do
  echo "=== $t"
  grep -E '^FAILED' "$t/verifier/test-stdout.txt" | sed 's/ - .*//'
  grep -E '^--- ' "$t/verifier/test-stdout.txt" | cut -c1-140 | sort -u
done
