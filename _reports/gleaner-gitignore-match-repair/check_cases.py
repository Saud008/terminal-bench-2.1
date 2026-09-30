#!/usr/bin/env python3
"""usage: check_cases.py cases.json BINARY -> per-group pass/fail of BINARY against recorded cases."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_cases import compare  # noqa: E402

groups = json.load(open(sys.argv[1], encoding="utf-8"))["groups"]
for name, cases in groups.items():
    fails = [(c["name"], why) for c in cases if (why := compare(sys.argv[2], c))]
    print(f"  {'FAIL' if fails else 'pass'} {name}: {len(fails)}/{len(cases)} " + "; ".join(f"{n}" for n, w in fails[:4]))
