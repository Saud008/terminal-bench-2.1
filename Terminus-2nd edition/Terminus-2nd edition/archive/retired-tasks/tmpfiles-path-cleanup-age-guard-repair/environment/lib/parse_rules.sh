#!/usr/bin/env bash

parse_rules_file() {
  local rules_file="$1"
  python3 - "$rules_file" <<'PY'
import json, sys

def parse_age(token):
    if token in ("-", ""):
        return None
    if token.isdigit():
        return int(token)
    num = int(token[:-1])
    unit = token[-1]
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}.get(unit)
    if mult is None:
        raise ValueError(token)
    return num * mult

rules = []
for raw in open(sys.argv[1], encoding="utf-8"):
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split()
    typ = parts[0]
    path = parts[1]
    row = {"type": typ, "path": path}
    if typ in ("d", "z", "o"):
        row.update(
            {
                "mode": parts[2] if len(parts) > 2 else "-",
                "user": parts[3] if len(parts) > 3 else "-",
                "group": parts[4] if len(parts) > 4 else "-",
                "age": parse_age(parts[5]) if len(parts) > 5 else None,
            }
        )
    elif typ in ("r", "r!"):
        row["type"] = "r!"
        row.update(
            {
                "mode": "-",
                "user": "-",
                "group": "-",
                "age": parse_age(parts[2]) if len(parts) > 2 else None,
                "exclude_depth": 0,
            }
        )
        for extra in parts[3:]:
            if extra.startswith("e") and extra[1:].isdigit():
                row["exclude_depth"] = int(extra[1:])
    elif typ == "x":
        row.update({"mode": "-", "user": "-", "group": "-", "age": None})
    else:
        continue
    rules.append(row)
print(json.dumps(rules))
PY
}
