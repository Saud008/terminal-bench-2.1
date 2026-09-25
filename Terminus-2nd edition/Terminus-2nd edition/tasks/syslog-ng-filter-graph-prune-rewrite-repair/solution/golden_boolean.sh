#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

msg_line="$1"
filters_path="$2"

IFS=',' read -r msg_id facility level program host text <<<"$msg_line"

match_atom() {
  local atom="$1"
  if [[ "$atom" == facility\(* ]]; then
    local want="${atom#facility(}"
    want="${want%)}"
    [ "$facility" = "$want" ]
  elif [[ "$atom" == level\(* ]]; then
    local want="${atom#level(}"
    want="${want%)}"
    [ "$level" = "$want" ]
  elif [[ "$atom" == program\(* ]]; then
    local want="${atom#program(}"
    want="${want%)}"
    [ "$program" = "$want" ]
  else
    return 1
  fi
}

unwrap_outer_parens() {
  local expr="$1"
  if [ "${expr:0:1}" != "(" ]; then
    echo "$expr"
    return 0
  fi
  local depth=0 idx=0 ch
  for ((idx=0; idx<${#expr}; idx++)); do
    ch="${expr:$idx:1}"
    if [ "$ch" = "(" ]; then
      depth=$((depth + 1))
    elif [ "$ch" = ")" ]; then
      depth=$((depth - 1))
      if [ "$depth" -eq 0 ] && [ "$idx" -eq $(( ${#expr} - 1 )) ]; then
        echo "${expr:1:${#expr}-2}"
        return 0
      fi
    fi
  done
  echo "$expr"
}

eval_atom() {
  local expr="$1"
  expr="${expr// /}"
  local inner
  inner="$(unwrap_outer_parens "$expr")"
  if [ "$inner" != "$expr" ]; then
    eval_or "$inner"
    return $?
  fi
  match_atom "$expr"
}

eval_and() {
  local expr="$1"
  expr="${expr// /}"
  local depth=0 idx=0 ch left right
  for ((idx=0; idx<${#expr}; idx++)); do
    ch="${expr:$idx:1}"
    if [ "$ch" = "(" ]; then
      depth=$((depth + 1))
    elif [ "$ch" = ")" ]; then
      depth=$((depth - 1))
    elif [ "$depth" -eq 0 ] && [ "$ch" = "&" ] && [ "${expr:$((idx+1)):1}" = "&" ]; then
      left="${expr:0:idx}"
      right="${expr:$((idx+2))}"
      eval_and "$left" && eval_or "$right"
      return $?
    fi
  done
  eval_atom "$expr"
}

eval_or() {
  local expr="$1"
  expr="${expr// /}"
  local depth=0 idx=0 ch left right
  for ((idx=0; idx<${#expr}; idx++)); do
    ch="${expr:$idx:1}"
    if [ "$ch" = "(" ]; then
      depth=$((depth + 1))
    elif [ "$ch" = ")" ]; then
      depth=$((depth - 1))
    elif [ "$depth" -eq 0 ] && [ "$ch" = "|" ] && [ "${expr:$((idx+1)):1}" = "|" ]; then
      left="${expr:0:idx}"
      right="${expr:$((idx+2))}"
      if eval_or "$left"; then
        return 0
      fi
      eval_and "$right"
      return $?
    fi
  done
  eval_and "$expr"
}

eval_expr() {
  eval_or "$1"
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
