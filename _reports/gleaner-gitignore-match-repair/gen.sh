#!/bin/bash
# usage: gen.sh  -> records cases.json from git 2.39 (container), re-records with WSL git 2.53 and requires identical output,
# then compares /bin-gl/gleaner (+ /bin-bug/gleaner if present)
set -euo pipefail
R="/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)"
D="$R/_reports/gleaner-gitignore-match-repair"
T="$R/gleaner-gitignore-match-repair/gleaner-gitignore-match-repair/tests"
mkdir -p /tmp/gl-bug
extra=""
[ -x /tmp/gl-bug/gleaner ] && extra="/bin-bug/gleaner"
docker run --rm -v "$D":/r:ro -v /tmp/gl-target/release:/bin-gl:ro -v /tmp/gl-bug:/bin-bug:ro -v "$T":/out gleaner-dev \
  bash -c "git --version; python3 /r/gen_cases.py /out/cases.json /bin-gl/gleaner $extra"
git --version
(cd /tmp && python3 "$D/gen_cases.py" /tmp/cases253.json >/dev/null)
if cmp -s /tmp/cases253.json "$T/cases.json"; then echo "git 2.39 and 2.53 recordings IDENTICAL"; else echo "!!! recordings DIFFER"; diff /tmp/cases253.json "$T/cases.json" | head -20; fi
