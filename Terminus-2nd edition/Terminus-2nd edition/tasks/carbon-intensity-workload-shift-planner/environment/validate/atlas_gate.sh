#!/usr/bin/env bash
# Atlas output path guard for publish subcommand smoke checks.
set -euo pipefail
test -d /app/output
