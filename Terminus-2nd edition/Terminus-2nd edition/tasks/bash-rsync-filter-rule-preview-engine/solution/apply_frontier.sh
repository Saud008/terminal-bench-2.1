#!/usr/bin/env bash
set -euo pipefail

patch -d /app -p1 --forward --batch < patches/ingest-ingest_tree.sh.patch
patch -d /app -p1 --forward --batch < patches/rules-parse_filters.sh.patch
patch -d /app -p1 --forward --batch < patches/rules-match_rule.sh.patch
patch -d /app -p1 --forward --batch < patches/cascade-cascade_stack.sh.patch
patch -d /app -p1 --forward --batch < patches/prune-prune_walk.sh.patch
patch -d /app -p1 --forward --batch < patches/delete-delete_risk.sh.patch
patch -d /app -p1 --forward --batch < patches/compile-compile_filters.sh.patch
patch -d /app -p1 --forward --batch < patches/atlas-preview_atlas.sh.patch

chmod +x /app/internal/rsfp93/ingest/ingest_tree.sh
chmod +x /app/internal/rsfp93/rules/parse_filters.sh
chmod +x /app/internal/rsfp93/rules/match_rule.sh
chmod +x /app/internal/rsfp93/cascade/cascade_stack.sh
chmod +x /app/internal/rsfp93/prune/prune_walk.sh
chmod +x /app/internal/rsfp93/delete/delete_risk.sh
chmod +x /app/internal/rsfp93/compile/compile_filters.sh
chmod +x /app/internal/rsfp93/atlas/preview_atlas.sh
