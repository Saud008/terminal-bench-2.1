#!/usr/bin/env bash
# Ingest phase — walk .la archives and populate the scan workspace (hot path).

lt_ingest_la_tree() {
  lt_graph_load "$@"
}
