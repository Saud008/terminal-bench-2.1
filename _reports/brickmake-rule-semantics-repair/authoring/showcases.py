"""Print the makefiles and steps of cases in the given groups."""

import json
import sys

cases = json.load(open(sys.argv[1], encoding="utf-8"))
groups = set(sys.argv[2:])
for name, c in cases.items():
    if c["group"] not in groups:
        continue
    print("=" * 70, name)
    for step in c["steps"]:
        if step[0] == "write":
            print(f"--- write {step[1]}\n{step[2]}", end="")
        else:
            print("---", " ".join(step))
