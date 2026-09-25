#!/usr/bin/env bash
set -euo pipefail
# Oracle deploy helper for scan (ingest) stage wrapper.
install -m 0644 /solution/files/inventory_engine.py /app/lib/inventory_engine.py
install -m 0755 /solution/files/scan_inventory.sh /app/lib/scan_inventory.sh
