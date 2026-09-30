#!/bin/bash
set -uo pipefail

mkdir -p /logs/verifier
chmod 0755 /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in tests/Dockerfile before running this script."
    exit 0
fi

PY=/opt/pytools/bin/python
TBENCH_TEST_ID="${TBENCH_TEST_ID:-}"
targets=(/tests/test_outputs.py)

if [ -n "$TBENCH_TEST_ID" ]; then
    selected=$("$PY" -c '
import json, sys
known = {t["id"] for t in json.load(open("/tests/test_manifest.json"))["tests"]}
wanted = [s.strip() for s in sys.argv[1].split(",") if s.strip()]
unknown = [w for w in wanted if w not in known]
if not wanted or unknown:
    sys.exit("unknown TBENCH_TEST_ID: " + (", ".join(unknown) or repr(sys.argv[1])))
print("\n".join("/tests/" + w for w in wanted))
' "$TBENCH_TEST_ID")
    if [ $? -ne 0 ]; then
        exit 0
    fi
    mapfile -t targets <<< "$selected"
fi

"$PY" -m pytest --ctrf /logs/verifier/ctrf.json "${targets[@]}" -rA
rc=$?

if [ "$rc" -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi

exit 0
