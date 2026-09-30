set -e
D='/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)/gleaner-gitignore-match-repair'
rm -rf "$D/trajectories"
cp -r /tmp/glprep/gleaner-gitignore-match-repair/trajectories "$D/"
cd "$D/trajectories"
cat SUMMARY.txt
for r in run-0*; do
  echo "== $r reward=$(cat $r/verifier/reward.txt) trial=$(python3 -c "import json;print(json.load(open('$r/result.json')).get('trial_name'))")"
done
python3 "/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)/_reports/gleaner-gitignore-match-repair/scrub_traj.py" . --apply
grep -rlE '/home/saud|/Users/|/private/tmp/|/mnt/c' . || echo "no host paths"
grep -rlwE 'stb' . || echo "no stb"
