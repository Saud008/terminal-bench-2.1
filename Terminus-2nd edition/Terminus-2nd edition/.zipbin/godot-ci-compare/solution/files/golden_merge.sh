#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

tscn_merge_three_way() {
  local base_text="$1" left_text="$2" right_text="$3" base_path="$4" left_path="$5" right_path="$6" base_name="$7"
  base_text="${base_text:-${TSCN_BASE_TEXT:-}}"
  left_text="${left_text:-${TSCN_LEFT_TEXT:-}}"
  right_text="${right_text:-${TSCN_RIGHT_TEXT:-}}"
  base_name="${base_name:-${TSCN_BASE_NAME:-base}}"
  python3 - "${base_text}" "${left_text}" "${right_text}" "${base_name}" <<'PY'
import sys

base_text, left_text, right_text, base_name = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

if left_text == base_text and right_text == base_text:
    print(base_text, end="")
elif left_text == base_text:
    print(right_text, end="")
elif right_text == base_text:
    print(left_text, end="")
elif left_text == right_text:
    print(left_text, end="")
else:
    print(base_text, end="")
PY
}
