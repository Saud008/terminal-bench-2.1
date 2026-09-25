#!/usr/bin/env bash
set -euo pipefail

version_gt() {
  local a="$1"
  local b="$2"
  python3 - <<'PY' "$a" "$b"
import sys

def parse(v):
    epoch = 0
    if ":" in v:
        e, rest = v.split(":", 1)
        epoch = int(e)
        v = rest
    if "-" in v:
        upstream, deb = v.rsplit("-", 1)
    else:
        upstream, deb = v, "0"
    return (epoch, upstream, deb)

def cmp_up(a, b):
    for x, y in zip(a.split("."), b.split(".")):
        if x == y:
            continue
        if x.isdigit() and y.isdigit():
            return (int(x) > int(y)) - (int(x) < int(y))
        return (x > y) - (x < y)
    return (len(a) > len(b)) - (len(a) < len(b))

def cmp_ver(a, b):
    ea, ua, da = parse(a)
    eb, ub, db = parse(b)
    if ea != eb:
        return ea - eb
    c = cmp_up(ua.replace("~", "\x00"), ub.replace("~", "\x00"))
    if c:
        return c
    return cmp_up(da, db)

sys.exit(0 if cmp_ver(sys.argv[1], sys.argv[2]) > 0 else 1)
PY
}
