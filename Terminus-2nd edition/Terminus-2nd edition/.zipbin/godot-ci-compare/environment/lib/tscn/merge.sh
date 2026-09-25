#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

tscn_merge_three_way() {
  local base_text="$1" left_text="$2" right_text="$3" base_path="$4" left_path="$5" right_path="$6" base_name="$7"
  base_text="${base_text:-${TSCN_BASE_TEXT:-}}"
  left_text="${left_text:-${TSCN_LEFT_TEXT:-}}"
  right_text="${right_text:-${TSCN_RIGHT_TEXT:-}}"
  base_path="${base_path:-${TSCN_BASE_PATH:-}}"
  left_path="${left_path:-${TSCN_LEFT_PATH:-}}"
  right_path="${right_path:-${TSCN_RIGHT_PATH:-}}"
  base_name="${base_name:-${TSCN_BASE_NAME:-base}}"
  python3 - "${base_text}" "${left_text}" "${right_text}" "${base_path}" "${left_path}" "${right_path}" "${base_name}" <<'PY'
import json, sys, os

base_text, left_text, right_text = sys.argv[1], sys.argv[2], sys.argv[3]
base_path, left_path, right_path, base_name = sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]

def mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return 0

if left_text == base_text and right_text == base_text:
    print(base_text, end="")
elif left_text == base_text:
    print(right_text, end="")
elif right_text == base_text:
    print(left_text, end="")
elif left_text == right_text:
    print(left_text, end="")
else:
    picks = [(mtime(left_path), left_text), (mtime(right_path), right_text)]
    picks.sort(reverse=True)
    print(picks[0][1], end="")
PY
}
