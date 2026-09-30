set -e
D='/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)/pinwheel-semver-range-repair'
rm -rf "$D/trajectories"
cp -r /tmp/pinprep/pinwheel-semver-range-repair/trajectories "$D/"
cd "$D/trajectories"
cat SUMMARY.txt
for r in run-0*; do
  echo "== $r reward=$(cat $r/verifier/reward.txt)"
  python3 - "$r" <<'PY'
import json, sys
r = sys.argv[1]
res = json.load(open(f"{r}/result.json"))
cfg = json.load(open(f"{r}/config.json"))
print(" trial:", res.get("trial_name"), "| exc:", res.get("exception_info"))
print(" cfg task.path:", cfg.get("task", {}).get("path"), "| trials_dir:", cfg.get("trials_dir"))
PY
done
grep -rlE '/home/saud|/Users/|/private/tmp/|/mnt/c' . || echo "no host paths"
grep -rlwE 'stb' . || echo "no stb"
