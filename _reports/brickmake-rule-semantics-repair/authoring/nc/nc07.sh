# NC-07 naive baseline: fixes only the two reported symptoms (pattern-variable order and the
# directory prefix), misses the stem-length and ought-to-exist rules found only in the docs.
set -e
bash /solution/solve.sh >/dev/null
python3 /a/ablate_one.py stem
python3 /a/ablate_one.py mention
cd /app && /usr/local/go/bin/go build ./...
