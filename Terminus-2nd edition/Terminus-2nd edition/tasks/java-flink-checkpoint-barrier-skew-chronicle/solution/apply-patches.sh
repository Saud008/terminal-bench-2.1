#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
patch -p1 --forward -d /app < patches/loader.patch
patch -p1 --forward -d /app < patches/mapper.patch
patch -p1 --forward -d /app < patches/watermark.patch
patch -p1 --forward -d /app < patches/chain.patch
patch -p1 --forward -d /app < patches/aligner.patch
