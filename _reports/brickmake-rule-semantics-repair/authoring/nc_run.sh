#!/bin/bash
# nc_run.sh <task-dir> [nc01 nc02 ...]: apply each shortcut in the agent image, run the real
# separate verifier on the resulting /app, print reward, per-test results and the first assertion.
set -u
T=$(realpath "$1"); shift
A=$(dirname "$(realpath "$0")")
docker build -q -t bm-agent "$T/environment" >/dev/null || exit 1
docker build -q -t bm-verify "$T/tests" >/dev/null || exit 1
for nc in "${@:-nc01 nc02 nc03 nc04 nc05 nc06 nc07 nc08 nc12 nc14}"; do
  for n in $nc; do
    echo "=== $n: $(sed -n 1p "$A/nc/$n.sh")"
    W=/tmp/bm-nc/$n; rm -rf "$W"; mkdir -p "$W/logs"
    docker rm -f bm-nc-agent >/dev/null 2>&1
    docker run --name bm-nc-agent -v "$T/solution:/solution:ro" -v "$A:/a:ro" bm-agent bash "/a/nc/$n.sh" >"$W/agent.log" 2>&1
    echo "agent exit: $?"
    docker cp bm-nc-agent:/app "$W/app"; docker rm -f bm-nc-agent >/dev/null; chmod -R a+rX "$W/app"
    docker run --rm -v "$W/app:/app" -v "$W/logs:/logs/verifier" bm-verify bash /tests/test.sh >"$W/stdout.txt" 2>&1
    echo "reward: $(cat "$W/logs/reward.txt")"
    grep -E '^(PASSED|FAILED|ERROR) ' "$W/stdout.txt" | sed 's/ - .*//'
    grep -m3 -E '^E  ' "$W/stdout.txt"
    mkdir -p "$A/nc_out" && cp "$W/stdout.txt" "$A/nc_out/$n.stdout.txt" && cp "$W/logs/reward.txt" "$A/nc_out/$n.reward.txt"
  done
done
