#!/bin/bash
# Local verifier loop (not Harbor): devloop.sh <task-dir> <mode> [patch-script]
#   mode = nop | oracle | patch   (patch runs the given script in the agent container instead of solve.sh)
set -uo pipefail
T=$(realpath "$1"); MODE=$2; PATCH=${3:-}
W=/tmp/bm-dev/$MODE; rm -rf "$W"; mkdir -p "$W/logs"
docker build -q -t bm-agent "$T/environment" >/dev/null || exit 1
docker build -q -t bm-verify "$T/tests" >/dev/null || exit 1
docker rm -f bm-dev-agent >/dev/null 2>&1
case $MODE in
  nop)    docker run --name bm-dev-agent bm-agent true ;;
  oracle) docker run --name bm-dev-agent -v "$T/solution:/solution:ro" bm-agent bash /solution/solve.sh >"$W/agent.log" 2>&1 ;;
  patch)  docker run --name bm-dev-agent -v "$(realpath "$PATCH"):/patch.sh:ro" bm-agent bash /patch.sh >"$W/agent.log" 2>&1 ;;
esac
echo "agent exit: $?"
docker cp bm-dev-agent:/app "$W/app"
docker rm -f bm-dev-agent >/dev/null
chmod -R a+rX "$W/app"
docker run --rm ${TBENCH_TEST_ID:+-e TBENCH_TEST_ID=$TBENCH_TEST_ID} -v "$W/app:/app" -v "$W/logs:/logs/verifier" bm-verify bash /tests/test.sh >"$W/stdout.txt" 2>&1
echo "reward: $(cat "$W/logs/reward.txt")"
grep -E '^(PASSED|FAILED|ERROR) ' "$W/stdout.txt" | sed 's/ - .*//'
