#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

msg_line="$1"
filters_path="$2"

IFS=',' read -r msg_id facility level program host text <<<"$msg_line"

eval_expr() {
  local expr="$1"
  expr="${expr// /}"
  expr="${expr//(/}"
  expr="${expr//)/}"

  eval_segment() {
    local segment="$1"
    local atom matched=1
    IFS='&&' read -ra atoms <<<"$segment"
    for atom in "${atoms[@]}"; do
      [ -z "$atom" ] && continue
      if [[ "$atom" == facility\(* ]]; then
        local want="${atom#facility(}"
        want="${want%)}"
        [ "$facility" = "$want" ] || matched=0
      elif [[ "$atom" == level\(* ]]; then
        local want="${atom#level(}"
        want="${want%)}"
        [ "$level" = "$want" ] || matched=0
      elif [[ "$atom" == program\(* ]]; then
        local want="${atom#program(}"
        want="${want%)}"
        [ "$program" = "$want" ] || matched=0
      else
        matched=0
      fi
    done
    [ "$matched" -eq 1 ]
  }

  IFS='||' read -ra parts <<<"$expr"
  for part in "${parts[@]}"; do
    if eval_segment "$part"; then
      return 0
    fi
  done
  return 1
}

lookup_filter() {
  local fid="$1"
  local line id expr
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    id="${line%%|*}"
    expr="${line#*|}"
    if [ "$id" = "$fid" ]; then
      echo "$expr"
      return 0
    fi
  done < "$filters_path"
  return 1
}

filter_id="$3"
expr="$(lookup_filter "$filter_id")"
eval_expr "$expr"
