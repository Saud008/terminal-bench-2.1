#!/bin/bash
# For each fix: solve.sh, then revert that one fix, then run the verifier.
set -u
T=$(realpath "$1")
A=$(dirname "$(realpath "$0")")
for fix in ${FIXES:-stem dirs mention patvars}; do
  cat > /tmp/bm-ablate-$fix.sh <<EOF
set -e
bash /solution/solve.sh >/dev/null
python3 /ablate_one.py $fix
cd /app && /usr/local/go/bin/go build ./... 
EOF
  echo "=== revert $fix"
  docker rm -f bm-dev-agent >/dev/null 2>&1
  W=/tmp/bm-dev/ablate-$fix; rm -rf "$W"; mkdir -p "$W/logs"
  docker run --name bm-dev-agent -v "$(realpath "$T")/solution:/solution:ro" -v "$A/ablate_one.py:/ablate_one.py:ro" \
      -v /tmp/bm-ablate-$fix.sh:/patch.sh:ro bm-agent bash /patch.sh >"$W/agent.log" 2>&1 || { echo "agent failed"; cat "$W/agent.log"; continue; }
  docker cp bm-dev-agent:/app "$W/app"; docker rm -f bm-dev-agent >/dev/null; chmod -R a+rX "$W/app"
  docker run --rm -v "$W/app:/app" -v "$W/logs:/logs/verifier" bm-verify bash /tests/test.sh >"$W/stdout.txt" 2>&1
  echo "reward: $(cat "$W/logs/reward.txt")"
  grep -E '^(PASSED|FAILED|ERROR) ' "$W/stdout.txt" | sed 's/ - .*//'
done
