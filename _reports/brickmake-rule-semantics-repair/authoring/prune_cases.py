"""Drop cases whose group is not in the kept list."""

import json
import sys

path = sys.argv[1]
keep = set(sys.argv[2:])
cases = json.load(open(path, encoding="utf-8"))
kept = {k: v for k, v in cases.items() if v["group"] in keep}
with open(path, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(kept, fh, indent=1, ensure_ascii=False)
    fh.write("\n")
print(f"kept {len(kept)} of {len(cases)} cases")
