#!/usr/bin/env bash
# Legacy merge helper — not on restore planner hot path.
merge_segments() {
  echo "$1 $2" | tr ' ' '\n' | sort -u
}
