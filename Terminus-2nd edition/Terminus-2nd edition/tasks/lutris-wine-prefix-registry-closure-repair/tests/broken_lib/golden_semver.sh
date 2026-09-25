#!/usr/bin/env bash
# DXVK semver pin check with numeric component comparison.

semver_pin_satisfied() {
  local version="$1"
  local pin="$2"
  local ok
  ok="$(python3 - "$version" "$pin" <<'PY'
import sys

def parse(v: str) -> tuple[int, int, int]:
    parts = v.strip().split(".")
    nums = []
    for i in range(3):
        if i < len(parts):
            nums.append(int(parts[i]))
        else:
            nums.append(0)
    return tuple(nums)

def satisfies(mod: str, req: str) -> bool:
    req = req.strip()
    if req.startswith(">="):
        return parse(mod) >= parse(req[2:])
    return mod == req

print("1" if satisfies(sys.argv[1], sys.argv[2]) else "0")
PY
)"
  [[ "$ok" == "1" ]]
}
