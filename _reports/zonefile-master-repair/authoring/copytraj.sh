#!/usr/bin/env bash
set -euo pipefail
DST="/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)/zonefile-master-repair"
mkdir -p "$DST/trajectories"
find "$DST/trajectories" -mindepth 1 -delete
cp -r ~/delivery_prep/zonefile-master-repair/trajectories/. "$DST/trajectories/"
cd "$DST/trajectories"
python3 "/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)/_reports/zonefile-master-repair/authoring/scrub.py" .
cat SUMMARY.txt
for r in run-0*; do echo "$r $(grep -o '"trial_name": "[^"]*"' $r/result.json | head -1) reward=$(cat $r/verifier/reward.txt)"; done
echo "-- leaks:"
grep -rlE '/home/saud|/Users/|/mnt/c|\bstb\b' . || echo none
echo "-- paths:"
grep -hoE '"(path|trials_dir|trial_uri|jobs_dir|task_dir)": "[^"]*"' run-0*/config.json run-0*/result.json | sort -u
