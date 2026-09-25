#!/usr/bin/env bash
# Tick timeline assembly from per-file descriptors and packets.

sd_parse_file_ticks() {
  local demo="$1"
  local rel_source="$2"
  local seed="$3"
  local work="$4"
  local out_ndjson="$5"

  read -r flags signon tc sc plen sio tio poff < <(sd_read_header "$demo")
  sd_load_strings "$demo" "${work}/strings.ndjson"
  local mask
  mask="$(sd_arg_mask "$seed" "$rel_source")"

  local TICK_BASE="$signon"
  local signon_resets=0
  : >"$out_ndjson"

  python3 - <<'PY' "$demo" "${work}/ticks.idx" "$tio" "$tc"
import struct, sys
from pathlib import Path
demo, out, tio, tc = sys.argv[1:5]
data = Path(demo).read_bytes()
rows = []
for i in range(int(tc)):
    rel, first, count, ord_, _ = struct.unpack_from("<IIHHI", data, int(tio) + i * 16)
    rows.append((rel, first, count, ord_))
Path(out).write_text("\n".join(f"{a} {b} {c} {d}" for a,b,c,d in rows) + ("\n" if rows else ""), encoding="utf-8")
PY

  local stream_file="${work}/packets.ndjson"
  sd_read_packets "$demo" "$poff" "$plen" "$stream_file" || return $?

  local passes=1
  if (( (flags & 1) != 0 )); then
    passes=2
  fi

  local pass=0
  while (( pass < passes )); do
    while IFS= read -r line; do
      [[ -n "$line" ]] || continue
      local rel first count ord_
      read -r rel first count ord_ <<<"$line"

      local slice="${work}/tick_slice.ndjson"
      python3 - <<'PY' "$stream_file" "$first" "$count" "$slice"
import json, sys
from pathlib import Path
src, first, count, out = sys.argv[1:5]
first, count = int(first), int(count)
picked = []
for i, line in enumerate(Path(src).read_text(encoding="utf-8").splitlines()):
    if first <= i < first + count:
        picked.append(line)
Path(out).write_text("\n".join(picked) + ("\n" if picked else ""), encoding="utf-8")
PY

      local global_tick=$((TICK_BASE + rel))
      while IFS= read -r pkt; do
        [[ -n "$pkt" ]] || continue
        local typ
        typ="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["type"])' "$pkt")"
        if [[ "$typ" == "signon_reset" ]]; then
          signon_resets=$((signon_resets + 1))
          continue
        fi
        if [[ "$typ" != "usercmd" ]]; then
          continue
        fi
        local str_idx seq arg salted
        read -r str_idx seq arg <<<"$(python3 - <<'PY' "$pkt"
import json, sys
p = json.loads(sys.argv[1])
print(p["str_idx"], p["seq"], p["arg"])
PY
)"
        local text
        text="$(sd_resolve_string "${work}/strings.ndjson" "$str_idx")"
        salted=$((arg ^ mask))
        SD_GTICK="$global_tick" SD_SOURCE="$rel_source" SD_SEQ="$seq" \
        SD_STRIDX="$str_idx" SD_TEXT="$text" SD_ARG="$salted" \
        python3 - <<'PY' >>"$out_ndjson"
import json, os
print(json.dumps({
    "global_tick": int(os.environ["SD_GTICK"]),
    "source": os.environ["SD_SOURCE"],
    "seq": int(os.environ["SD_SEQ"]),
    "str_idx": int(os.environ["SD_STRIDX"]),
    "string": os.environ["SD_TEXT"],
    "arg": int(os.environ["SD_ARG"]),
}))
PY
      done <"$slice"
    done <"${work}/ticks.idx"
    pass=$((pass + 1))
    sd_read_packets "$demo" "$poff" "$plen" "$stream_file" || true
  done

  printf '%s\n' "$signon_resets" >"${work}/signon_resets.count"
}
