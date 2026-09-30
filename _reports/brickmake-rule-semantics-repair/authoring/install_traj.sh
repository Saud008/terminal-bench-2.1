#!/bin/bash
# install_traj.sh: archive the TB 2.1 trajectories and install the assembled TB 4.0 ones.
set -e
S=brickmake-rule-semantics-repair
mkdir -p _archive/$S-tb21
[ -d $S/trajectories ] && mv $S/trajectories _archive/$S-tb21/trajectories
cp -r /tmp/bm-delivery/$S/trajectories $S/trajectories
for r in $S/trajectories/run-0*; do
  trial=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["trial_name"])' "$r/result.json")
  echo "$(basename $r) $trial reward=$(cat $r/verifier/reward.txt)"
done
cat $S/trajectories/SUMMARY.txt
