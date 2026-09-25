#!/usr/bin/env bash
# Ingest alias for load stage (systemd timer bundle merge).
exec bash "$(dirname "$0")/load.sh" "$@"
