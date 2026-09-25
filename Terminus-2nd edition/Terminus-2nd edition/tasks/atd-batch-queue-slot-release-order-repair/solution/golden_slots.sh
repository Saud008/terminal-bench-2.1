#!/usr/bin/env bash

allocate_letter() {
  local start_letter="$1"
  local seq_val="$2"
  python3 - "$start_letter" "$SPOOL_DIR" "$BATCH_SLOTS" <<'PY'
import string, sys
from pathlib import Path
start, spool, slots = sys.argv[1:4]
spool_dir = Path(spool)
slot_dir = Path(slots)
letters = string.ascii_lowercase
start_idx = letters.index(start)
for letter in letters[start_idx:]:
    if (slot_dir / letter).is_file():
        continue
    occupied = any(p.is_file() for p in spool_dir.glob(f"{letter}*"))
    if occupied:
        continue
    print(letter)
    break
else:
    print("")
PY
}

letter_spool_exists() {
  local letter="$1"
  local f
  for f in "${SPOOL_DIR}/${letter}"*; do
    if [[ -f "$f" ]]; then
      return 0
    fi
  done
  return 1
}
