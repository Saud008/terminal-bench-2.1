# NC-05 one declared artifact missing: the engine is fixed but /app/cmd/brickmake is gone.
set -e
bash /solution/solve.sh >/dev/null
rm -rf /app/cmd/brickmake
