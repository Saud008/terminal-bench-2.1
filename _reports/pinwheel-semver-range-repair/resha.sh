set -e
D='/mnt/c/Users/masau/Downloads/Terminus-2nd edition (1)/pinwheel-semver-range-repair'
cd "$D/pinwheel-semver-range-repair"
file task.toml
SHA=$(find instruction.md tests environment solution task.toml -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | cut -c1-16)
echo "sha=$SHA"
S="$D/trajectories/SUMMARY.txt"
sed -i -E "1s/sha=[0-9a-f]{16}/sha=$SHA/" "$S"
cat "$S"
od -c "$S" | tail -3
