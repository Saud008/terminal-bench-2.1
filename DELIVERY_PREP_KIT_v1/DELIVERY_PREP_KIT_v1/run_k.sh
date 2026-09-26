#!/usr/bin/env bash
# run_k.sh <task_dir> <k> [label]   — frontier reference arm, FULL-FIDELITY capture (F-129)
#   model @openai/gpt-5.6 (override MODEL=...), reasoning_effort xhigh (override EFFORT=...)
#   observation cap raised to 100 MB, all messages stored, raw API log, asciinema recording, console log, sha-bound SOURCE.txt
# Output: $OUT/<slug>-<label>-<stamp>/  (default OUT=./runs)
set -uo pipefail
TASK="$(cd "$1" && pwd)"; K="${2:-5}"; LABEL="${3:-k$K}"
SLUG="$(basename "$TASK")"; STAMP="$(date +%Y%m%d-%H%M%S)"
KIT="$(cd "$(dirname "$0")" && pwd)"
OUT="${OUT:-$PWD/runs}"; mkdir -p "$OUT"
JOB="$SLUG-$LABEL-$STAMP"; LOG="$OUT/$JOB.console.log"
MODEL="${MODEL:-@openai/gpt-5.6}"; EFFORT="${EFFORT:-xhigh}"; CONC="${CONC:-$K}"
find "$TASK" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; find "$TASK" -name .DS_Store -delete 2>/dev/null
SHA="$(cd "$TASK" && find instruction.md tests environment solution task.toml -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | cut -c1-16)"
# Verify first, refresh only if verify actually fails. Each `stb keys refresh` mints a new,
# separately-capped credential slice out of the shared budget rather than topping up the
# existing one -- refreshing unconditionally before every attempt (the old behaviour here)
# fragments a large budget into many mostly-unused small slices and burns the daily refresh
# quota for no reason when the current key is still perfectly valid. Refresh is for when the
# CLI itself flags the key as bad, not a preemptive habit.
stb keys verify >/dev/null 2>&1 || {
  echo "stb credentials invalid, refreshing once..."
  stb keys refresh >/dev/null 2>&1
  stb keys verify >/dev/null 2>&1 || { echo "stb credentials not valid — run: stb login --env prod && stb keys refresh"; exit 2; }
}
# Patch guard. The old inline probe tested BEHAVIOUR only, so stale bytecode or a
# PYTHONPATH shadow could make it pass over an unpatched source -- a false PASS in
# front of a paid round. patch_stb_harbor.py --check verifies source markers,
# in-module markers, behaviour, import provenance, harbor version and content
# digests together. Re-run it before EVERY attempt: any `uv tool install
# snorkelai-stb ... --reinstall` silently reverts the patch, including the one stb
# itself prints when it blocks on an outdated version.
python3 "$KIT/patch_stb_harbor.py" --check \
  || { echo "stb-bundled harbor is not patched -- run: python3 $KIT/patch_stb_harbor.py"; exit 3; }
echo "job $JOB  model $MODEL effort $EFFORT k=$K  bundle sha $SHA" | tee "$LOG"
export TERMINUS_MAX_OUTPUT_BYTES=100000000
export TERMINUS_RAW_API_LOG=1
stb harbor run -p "$TASK" -a terminus-2 -m "$MODEL" \
  --ak reasoning_effort="$EFFORT" --ak store_all_messages=true --ak 'llm_kwargs={"litellm_debug":true}' \
  -k "$K" -n "$CONC" -o "$OUT" --job-name "$JOB" --force-build -y >> "$LOG" 2>&1
RC=$?; echo "harbor rc=$RC" | tee -a "$LOG"
cat > "$OUT/$JOB/SOURCE.txt" <<EOS
job $JOB, task $SLUG, bundle sha $SHA, model $MODEL, reasoning_effort $EFFORT, k=$K, agent terminus-2,
TERMINUS_MAX_OUTPUT_BYTES=$TERMINUS_MAX_OUTPUT_BYTES, store_all_messages=true, raw API log (api-calls.jsonl) on,
arch $(uname -m), run $(date +%F) via stb $(stb --version 2>/dev/null | awk '{print $3}'), console log $LOG
EOS
python3 "$KIT/check_trajectory.py" "$OUT/$JOB" | tee -a "$LOG"
