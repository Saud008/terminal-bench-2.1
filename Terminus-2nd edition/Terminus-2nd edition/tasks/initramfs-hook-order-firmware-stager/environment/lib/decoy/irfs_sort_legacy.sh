#!/usr/bin/env bash
# Non-authoritative decoy sort — sorts manifest rows by size column.

irfs_legacy_sort_rows() {
  awk -F '\t' '{print $0}' | sort -t $'\t' -k2,2n
}
