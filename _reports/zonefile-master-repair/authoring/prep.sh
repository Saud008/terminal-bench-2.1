#!/usr/bin/env bash
set -uo pipefail
ROOT="/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)"
KIT="$ROOT/DELIVERY_PREP_KIT_v1/DELIVERY_PREP_KIT_v1"
rm -rf ~/delivery_prep/zonefile-master-repair
mkdir -p ~/delivery_prep
python3 "$KIT/delivery_prep.py" zonefile-master-repair \
  --ingested "$ROOT" \
  --jobs ~/tbruns/zonefile-master-repair-k2-20260927-052835 ~/tbruns/zonefile-master-repair-k3-20260927-055035 \
  --out ~/delivery_prep --max-trials 5 2>&1 | tail -40
