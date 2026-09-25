#!/usr/bin/env bash
# Parse .gitattributes and resolve filter=gcrypt paths.

# shellcheck source=gc_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/gc_common.sh"

GC_ATTR_CACHE_FILE=""
GC_ATTR_LINES=()

gc_attrs_load() {
  local repo="$1"
  GC_ATTR_CACHE_FILE="${repo}/.gitattributes"
  GC_ATTR_LINES=()
  [[ -f "$GC_ATTR_CACHE_FILE" ]] || return 1
  local line
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="$(gc__trim "$line")"
    [[ -z "$line" || "$line" == \#* ]] && continue
    GC_ATTR_LINES+=("$line")
  done < "$GC_ATTR_CACHE_FILE"
}

gc_attrs__glob_match() {
  local pattern="$1"
  local path="$2"
  python3 - "$pattern" "$path" <<'PY'
import fnmatch
import sys

pat, path = sys.argv[1], sys.argv[2]
print("1" if fnmatch.fnmatch(path, pat) else "0")
PY
}

gc_attrs__score() {
  local pattern="$1"
  local lineno="$2"
  if [[ "$pattern" != *"*"* && "$pattern" != *"?"* ]]; then
    printf '%d' $((10000 + ${#pattern}))
    return
  fi
  local slashes="${pattern//[^\/]/}"
  local lit="${pattern//[\*\?]/}"
  printf '%d' $((100 * ${#lit} + 10 * ${#slashes} + lineno))
}

gc_attrs__winner() {
  local relpath="$1"
  local best_score=-1
  local best_filter=""
  local best_spec=0
  local lineno=0
  local best_lineno=0
  local line pattern attrs neg
  for line in "${GC_ATTR_LINES[@]}"; do
    lineno=$((lineno + 1))
    neg=0
    pattern="$line"
    if [[ "$pattern" == !* ]]; then
      neg=1
      pattern="${pattern#!}"
      pattern="$(gc__trim "$pattern")"
    fi
    attrs="${pattern#* }"
    pattern="${pattern%% *}"
    pattern="$(gc__trim "$pattern")"
    [[ "$(gc_attrs__glob_match "$pattern" "$relpath")" == "1" ]] || continue
    local score
    score="$(gc_attrs__score "$pattern" "$lineno")"
    local filt=""
    if [[ "$neg" -eq 1 || "$attrs" == *-filter* ]]; then
      filt=""
    elif [[ "$attrs" == *filter=gcrypt* ]]; then
      filt="gcrypt"
    fi
    if [[ $score -gt $best_score || ( $score -eq $best_score && $lineno -gt $best_lineno ) ]]; then
      best_score=$score
      best_lineno=$lineno
      best_filter="$filt"
      best_spec=$score
    fi
  done
  GC_ATTR_WIN_FILTER="$best_filter"
  GC_ATTR_WIN_SPEC="$best_spec"
}

gc_attrs_filter_active() {
  local repo="$1"
  local relpath="$2"
  gc_attrs_load "$repo" || return 1
  gc_attrs__winner "$relpath"
  [[ "$GC_ATTR_WIN_FILTER" == "gcrypt" ]]
}

gc_attrs_winning_filter() {
  local repo="$1"
  local relpath="$2"
  gc_attrs_load "$repo" || return 1
  gc_attrs__winner "$relpath"
  printf '%s' "$GC_ATTR_WIN_FILTER"
}

gc_attrs_specificity() {
  local repo="$1"
  local relpath="$2"
  gc_attrs_load "$repo" || return 1
  gc_attrs__winner "$relpath"
  printf '%d' "$GC_ATTR_WIN_SPEC"
}
