#!/usr/bin/env bash
# Run immediately after creating or major-editing a task tree (Phase D).
# Anti-spam post-create + oracle/NOP reminder. See new-task-pipeline-A-H.mdc.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<EOF
Usage: $(basename "$0") <task-name> [--rebuild-index] [--llm-judge]

Locates tasks/<name>/ or pending/<name>/, runs anti-spam post-create gate,
then prints Harbor oracle/NOP commands for Phase F.

Exit 0 = Anti-spam/templated PASS · Exit 1 = FAIL (fix in place before audit/zip)
EOF
  exit 1
}

TASK_NAME=""
REBUILD=""
LLM=""

while [ $# -gt 0 ]; do
  case "$1" in
    --rebuild-index) REBUILD="--rebuild-index"; shift ;;
    --llm-judge) LLM="--llm-judge"; shift ;;
    -h|--help) usage ;;
    *)
      if [ -z "$TASK_NAME" ]; then
        TASK_NAME="$1"
        shift
      else
        echo "Unknown argument: $1" >&2
        usage
      fi
      ;;
  esac
done

[ -n "$TASK_NAME" ] || usage

TASK_DIR=""
for base in tasks pending; do
  if [ -d "$REPO_ROOT/$base/$TASK_NAME" ] && [ -f "$REPO_ROOT/$base/$TASK_NAME/task.toml" ]; then
    TASK_DIR="$REPO_ROOT/$base/$TASK_NAME"
    break
  fi
done

if [ -z "$TASK_DIR" ]; then
  echo "ERROR: no task dir with task.toml: tasks/$TASK_NAME/ or pending/$TASK_NAME/" >&2
  exit 1
fi

python=""
for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    python="$cmd"
    break
  fi
done

if [ -z "$python" ]; then
  echo "ERROR: python3 not found" >&2
  exit 1
fi

echo "=== Anti-spam post-create: $TASK_NAME ==="
set +e
"$python" "$REPO_ROOT/scripts/terminus_anti_spam_auto.py" post-create \
  --task-dir "$TASK_DIR" $REBUILD $LLM
RC=$?
set -e

echo ""
echo "=== CREATE finish (Phases E→F→F′→G) ==="
echo "  $REPO_ROOT/scripts/create_finish_to_zip.sh $TASK_NAME"
echo ""
echo "Runs: static audit gate → Harbor oracle/NOP → ruff → F′ record → pack_zip.sh"
echo "Agent: fix High/Medium if exit 2; re-run until tasksubmit/$TASK_NAME.zip exists."
echo ""
echo "Harbor only (manual):"
echo "  cd \"$TASK_DIR\""
echo "  harbor run -a oracle -p . --debug --force-build"
echo "  harbor run -a nop -p . --debug --force-build"
echo "  $REPO_ROOT/scripts/create_finish_to_zip.sh $TASK_NAME --skip-harbor --oracle 1.0 --nop 0.0"
echo ""
echo "Report: $REPO_ROOT/jobs-local/anti-spam-post-create-last.json"

echo ""
echo "=== Phase E auto audit — round 1 static gate ==="
"$python" "$REPO_ROOT/scripts/post_create_audit_loop.py" --task-dir "$TASK_DIR" --round 1 || RC=$?

echo ""
echo "Report: $REPO_ROOT/jobs-local/post-create-audit-last.json"
echo "Policy: archive/terminus-rules-mdc/create/post-create-audit-loop.mdc (agent runs 2–4 rounds)"

echo ""
echo "=== Full pipeline (E→F→F′→G) — automatic ==="
"$python" "$REPO_ROOT/scripts/create_finish_to_zip.py" --task-dir "$TASK_DIR" || RC=$?

echo ""
echo "Report: $REPO_ROOT/jobs-local/create-finish-last.json"
if [ -f "$REPO_ROOT/tasksubmit/$TASK_NAME.zip" ]; then
  echo "ZIP: $REPO_ROOT/tasksubmit/$TASK_NAME.zip"
fi

exit "$RC"
