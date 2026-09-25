#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/wcs-cache/* /app/work/detection-buffer/* /app/work/xmatch-buffer/* /app/output/*
mkdir -p /app/state/wcs-cache /app/work/detection-buffer /app/work/xmatch-buffer /app/output
