cd ~/tbruns/"$1" || exit 1
for t in pinwheel*/; do
  echo "=== $t"
  grep -E '^(FAILED|PASSED)|go build failed|source policy' "$t/verifier/test-stdout.txt" | head -20
  grep -E '^E  ' "$t/verifier/test-stdout.txt" | head -25
done
