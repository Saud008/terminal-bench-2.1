#!/bin/bash
set -euo pipefail
D="/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)"
T="$D/gleaner-gitignore-match-repair/gleaner-gitignore-match-repair/tests/cases.json"
git --version
cd /tmp
python3 "$D/_reports/gleaner-gitignore-match-repair/gen_cases.py" /tmp/cases253.json >/dev/null
cmp /tmp/cases253.json "$T" && echo "git 2.53 re-recording IDENTICAL to tests/cases.json"
sha256sum /tmp/cases253.json "$T" | cut -c1-16
