cd ~/tbruns/"$1" || exit 1
for t in gleaner*/; do
  echo "=== $t"
  grep -E '^(FAILED|PASSED)|cargo build failed|source policy' "$t/verifier/test-stdout.txt" | grep -v PASSED | head -20
  grep -E '^E  ' "$t/verifier/test-stdout.txt" | head -${2:-25}
done
