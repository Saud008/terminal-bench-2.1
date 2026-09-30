#!/bin/bash
# runinfo.sh <trial-id-suffix>: failing tests and first assertions of a run_k trial (or its exception).
d=$(find runs -maxdepth 3 -type d -name "*$1" | head -1)
echo "$d"
if [ -f "$d/exception.txt" ]; then
  grep -v '^\s*$' "$d/exception.txt" | grep -iE 'error|failed|denied|conflict|no space|network|pull|port|exit' | tail -15 | cut -c1-400
  exit 0
fi
grep -E '^(PASSED|FAILED)' "$d/verifier/test-stdout.txt"
grep -m8 -E '^E  ' "$d/verifier/test-stdout.txt" | cut -c1-500
