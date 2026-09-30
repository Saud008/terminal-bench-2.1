"""merge_extra.py <gen-output.txt> <cases.json>: append the cases printed by gen_expect.py."""
import json
import sys

text = open(sys.argv[1], encoding="utf-8").read()
extra = json.loads(text[text.index("mismatches\n") + len("mismatches\n"):])
cases = json.load(open(sys.argv[2], encoding="utf-8"))
for name, case in extra.items():
    cases[f"{case['group']}/{name}"] = case
with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as fh:
    json.dump(cases, fh, indent=1)
    fh.write("\n")
print(f"{len(cases)} cases")
