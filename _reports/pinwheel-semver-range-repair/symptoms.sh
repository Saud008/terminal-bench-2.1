cd /app
pinwheel compare 2.1.0-beta.11 2.1.0-beta.2
for p in storefront ledger-cli batch-worker; do
  echo "== $p"
  pinwheel resolve "examples/$p"; echo "rc=$?"
  [ -f "examples/$p/pin.lock" ] && cat "examples/$p/pin.lock"
done
