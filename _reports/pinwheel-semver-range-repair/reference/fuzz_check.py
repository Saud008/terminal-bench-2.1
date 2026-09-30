import json
import subprocess
import sys

data = json.load(open(sys.argv[1]))
binary = sys.argv[2]
bad = 0
for v, r, want in data["sat"]:
    out = subprocess.run([binary, "satisfies", v, r], capture_output=True, text=True)
    got = out.stdout.strip()
    if out.returncode != 0 or got != str(want).lower():
        bad += 1
        if bad <= 20:
            print("SAT MISMATCH", v, repr(r), want, out.returncode, got, out.stderr.strip())
for a, b, want in data["cmp"]:
    out = subprocess.run([binary, "compare", a, b], capture_output=True, text=True)
    if out.stdout.strip() != str(want):
        bad += 1
        if bad <= 40:
            print("CMP MISMATCH", a, b, want, out.stdout.strip())
print("mismatches:", bad, "of", len(data["sat"]) + len(data["cmp"]))
