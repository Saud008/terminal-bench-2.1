#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_DIR="${ROOT_DIR}/patches"

patch -p1 --forward --silent < "${PATCH_DIR}/credmatch__cred_floor.go.patch"
patch -p1 --forward --silent < "${PATCH_DIR}/districtgate__hold_mask.go.patch"
patch -p1 --forward --silent < "${PATCH_DIR}/calendarblock__calendar_span.go.patch"
patch -p1 --forward --silent < "${PATCH_DIR}/priorscore__violation_prior.go.patch"
patch -p1 --forward --silent < "${PATCH_DIR}/laneassign__lane_router.go.patch"
patch -p1 --forward --silent < "${PATCH_DIR}/manifestemit__emit_manifest.go.patch"
patch -p1 --forward --silent < "${PATCH_DIR}/rankengine__rank_permits.go.patch"

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
