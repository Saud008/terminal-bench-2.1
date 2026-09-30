#!/usr/bin/env bash
cd ~/tbruns || exit 1
d=$(ls -td zonefile-master-repair-k3-2*/ | head -1)
echo "job $d"
for t in "$d"*/; do
  n=$(wc -l < "$t/agent/api-calls.jsonl" 2>/dev/null)
  r=$(cat "$t/verifier/reward.txt" 2>/dev/null)
  echo "$t api=$n reward=$r"
done
grep -E '^(OK|BAD|SUMMARY|harbor rc)' ~/tbruns/zmr-k3-driver.log
