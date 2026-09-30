#!/bin/bash
# prep.sh: assemble the 5 trials (k=2 + replacement k=3) with the kit's delivery_prep.py into /tmp/bm-delivery.
S=brickmake-rule-semantics-repair
rm -rf /tmp/bm-delivery
python3 DELIVERY_PREP_KIT_v1/DELIVERY_PREP_KIT_v1/delivery_prep.py "$S" \
  --ingested . \
  --jobs runs/$S-k2-20260930-092720 runs/$S-k3-20260930-094016 \
  --out /tmp/bm-delivery
echo "rc=$?"
find /tmp/bm-delivery -maxdepth 3 -type d | sort
cat /tmp/bm-delivery/$S/trajectories/SUMMARY.txt 2>/dev/null
