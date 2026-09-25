#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
patch -p1 --forward -d /app < oracle-patches/velocity_table.go.patch
patch -p1 --forward -d /app < oracle-patches/capacity_margin.go.patch
patch -p1 --forward -d /app < oracle-patches/pallet_remainder.go.patch
patch -p1 --forward -d /app < oracle-patches/shift_fit.go.patch
patch -p1 --forward -d /app < oracle-patches/task_upsert.go.patch
patch -p1 --forward -d /app < oracle-patches/schedule_writer.go.patch
patch -p1 --forward -d /app < oracle-patches/lane_bias.go.patch
patch -p1 --forward -d /app < oracle-patches/replen_wave.go.patch
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
