"""Replay scenarios through real GNU make 4.3 (make -r -R) and print the expected results.

Run inside debian:bookworm with make + python3, tests mounted at /tests:
  python3 gen_expect.py /tests/cases.json [extra.json]
For every case in cases.json it compares GNU make's output with the stored expectation;
for every case in extra.json it prints the expectation to paste into cases.json.
"""

import json
import os
import re
import sys

sys.path.insert(0, "/tests")
import harness  # noqa: E402

WRAPPER = "/usr/local/bin/gm"
with open(WRAPPER, "w") as fh:
    fh.write('#!/bin/bash\nexec -a make /usr/bin/make -r -R "$@"\n')
os.chmod(WRAPPER, 0o755)


def rename(results):
    fixed = []
    for r in results:
        r = dict(r)
        for k in ("stdout", "stderr"):
            if k in r:
                r[k] = re.sub(r"(?m)^make:", "brickmake:", r[k])
        fixed.append(r)
    return fixed


def replay(case):
    return rename(harness.play(case["steps"], WRAPPER))


bad = 0
with open(sys.argv[1]) as fh:
    for name, case in json.load(fh).items():
        got = replay(case)
        if got != case["expect"]:
            bad += 1
            print(f"MISMATCH {name}\n  stored: {case['expect']!r}\n  gnu:    {got!r}")
        else:
            print(f"ok {name}")
print(f"{bad} mismatches")
if len(sys.argv) > 2:
    with open(sys.argv[2]) as fh:
        extra = json.load(fh)
    for case in extra.values():
        case["expect"] = replay(case)
    print(json.dumps(extra, indent=1))
