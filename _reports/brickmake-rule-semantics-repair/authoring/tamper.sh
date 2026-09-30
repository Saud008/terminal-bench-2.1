#!/bin/bash
# tamper.sh <task-dir>: flip one baked GNU make expectation in a copy of tests/ and confirm the
# oracle is then rejected by exactly the test that owns that scenario (check 45).
set -u
T=$(realpath "$1"); C=/tmp/bm-tamper; rm -rf "$C"; cp -r "$T" "$C"
python3 - "$C/tests/cases.json" <<'EOF'
import json, sys
p = sys.argv[1]
cases = json.load(open(p))
c = cases["mention/order_only_mention_counts_too"]
first = next(r for r in c["expect"] if "stdout" in r)
first["stdout"] = first["stdout"].replace("\n", " \n", 1)
json.dump(cases, open(p, "w"), indent=1)
print("tampered mention/order_only_mention_counts_too stdout (one trailing space)")
EOF
docker build -q -t bm-verify-tamper "$C/tests" >/dev/null || exit 1
W=/tmp/bm-dev/tamper; rm -rf "$W"; mkdir -p "$W/logs"
docker rm -f bm-tamper-agent >/dev/null 2>&1
docker run --name bm-tamper-agent -v "$T/solution:/solution:ro" bm-agent bash /solution/solve.sh >/dev/null 2>&1
docker cp bm-tamper-agent:/app "$W/app"; docker rm -f bm-tamper-agent >/dev/null; chmod -R a+rX "$W/app"
docker run --rm -v "$W/app:/app" -v "$W/logs:/logs/verifier" bm-verify-tamper bash /tests/test.sh >"$W/stdout.txt" 2>&1
echo "reward: $(cat "$W/logs/reward.txt")"
grep -E '^(PASSED|FAILED|ERROR) ' "$W/stdout.txt" | sed 's/ - .*//'
grep -m1 -E '^E       AssertionError' "$W/stdout.txt"
