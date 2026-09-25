#!/usr/bin/env bash
# LOCKED pack path — tasks/<name>/ → tasksubmit/<name>.zip per @ZIP RULES
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<EOF
Usage:
  $(basename "$0") <task-name> [--milestone]
  $(basename "$0") --all

  tasks/<task-name>/  →  tasksubmit/<task-name>.zip
  --all               →  pack every task under tasks/ (skips _accepted-tasks, WIP without harness)
EOF
  exit 1
}

ZIP_EXCLUDES=(
  -x "**/.pytest_cache/*"
  -x "**/.pytest_cache/**"
  -x "**/.ruff_cache/*"
  -x "**/.ruff_cache/**"
  -x "**/.ruff_cache"
  -x "*/.ruff_cache/*"
  -x ".ruff_cache/*"
  -x ".ruff_cache/**"
  -x "output/*"
  -x "jobs/**"
  -x "**/__pycache__/*"
  -x "**/*.pyc"
  -x "environment/target/*"
  -x "environment/app/build/*"
  -x "**/node_modules/*"
  -x "**/dist/*"
  -x "rubric.md"
  -x "**/rubric.md"
)

is_milestone_task() {
  local task_dir="$1"
  [ -d "$task_dir/steps" ] && [ -f "$task_dir/task.toml" ]
}

pack_one() {
  local task_name="$1"
  local force_milestone="${2:--1}" # -1=auto, 0=no, 1=yes

  local task_dir="$REPO_ROOT/tasks/$task_name"
  if [ ! -d "$task_dir" ] && [ -d "$REPO_ROOT/pending/$task_name" ]; then
    task_dir="$REPO_ROOT/pending/$task_name"
  fi
  local out_dir="$REPO_ROOT/tasksubmit"
  local out_zip="$out_dir/$task_name.zip"
  local milestone=0

  if [ ! -d "$task_dir" ]; then
    echo "ERROR: Task not found: $task_dir" >&2
    return 1
  fi

  if [ "$force_milestone" -eq 1 ]; then
    milestone=1
  elif [ "$force_milestone" -eq 0 ]; then
    milestone=0
  elif is_milestone_task "$task_dir"; then
    milestone=1
  fi

  if [ "$milestone" -eq 1 ]; then
    for r in task.toml environment steps; do
      if [ ! -e "$task_dir/$r" ]; then
        echo "ERROR: Missing required: $r in $task_dir" >&2
        return 1
      fi
    done
  else
    for r in instruction.md task.toml environment tests solution; do
      if [ ! -e "$task_dir/$r" ]; then
        echo "ERROR: Missing required: $r in $task_dir" >&2
        return 1
      fi
    done
  fi

  if ! command -v zip >/dev/null 2>&1; then
    echo "ERROR: 'zip' not found. On Mac: xcode-select --install" >&2
    return 1
  fi

  local python=""
  for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
      python="$cmd"
      break
    fi
  done

  local dockerfile="$task_dir/environment/Dockerfile"
  if [ -f "$dockerfile" ] && [ -n "$python" ]; then
    if ! "$python" "$REPO_ROOT/scripts/migrate_dockerfile_canonical_ecr.py" --ensure --quiet --task-dir "$task_dir"; then
      echo "ERROR: Canonical ECR base image required before zip (see .cursor/rules/shared/canonical-base-image-gate.mdc)" >&2
      echo "       Auto-fix failed — edit environment/Dockerfile or run: python3 scripts/migrate_dockerfile_canonical_ecr.py --task-dir tasks/$task_name" >&2
      return 1
    fi
  fi

  if [ -f "$task_dir/task.toml" ] && [ -n "$python" ]; then
    if ! "$python" "$REPO_ROOT/scripts/ensure_subcategories_empty.py" --ensure --quiet --task-dir "$task_dir"; then
      echo "ERROR: task.toml must have subcategories = [] (see .cursor/rules/shared/task-toml-subcategories-gate.mdc)" >&2
      return 1
    fi
    if ! "$python" "$REPO_ROOT/scripts/ensure_category_allowed.py" --check --quiet --task-dir "$task_dir"; then
      echo "ERROR: task.toml category blocked for this project (see .cursor/rules/shared/task-toml-category-gate.mdc)" >&2
      return 1
    fi
    if [ "${TERMINUS_TASK_TOML_FIELDS_SKIP:-0}" != "1" ]; then
      if ! "$python" "$REPO_ROOT/scripts/ensure_task_toml_supported_fields.py" --check --quiet --task-dir "$task_dir"; then
        echo "ERROR: task.toml has unsupported/undocumented fields (see .cursor/rules/shared/task-toml-supported-fields-only.mdc)" >&2
        echo "       Remove invented metadata; use only official skeleton keys. Override (explicit only): TERMINUS_TASK_TOML_FIELDS_SKIP=1" >&2
        return 1
      fi
    fi
    if [ "${TERMINUS_TASK_GENERATION_SKIP:-0}" != "1" ]; then
      if ! "$python" "$REPO_ROOT/scripts/repository_state_gate.py" --pack-gate --quiet --task-dir "$task_dir"; then
        echo "ERROR: Repository-state gate failed — hard acceptance 7/7 required" >&2
        if [ -f "$REPO_ROOT/jobs-local/repository-state-gate-last.json" ] && \
           grep -q '"regenerate_required": true' "$REPO_ROOT/jobs-local/repository-state-gate-last.json" 2>/dev/null; then
          echo "       VERDICT: REGENERATE — forbidden repair/debug objective" >&2
          echo "       Policy: shared/forbidden-repair-objectives-gate.mdc" >&2
          echo "       Regenerate task (new slug, build-on-working-baseline) — do not patch in place." >&2
        fi
        echo "       Policy: shared/repository-state-requirement.mdc" >&2
        echo "       FAIL → fix: shared/repository-state-fail-fix.mdc (LOCKED — fix in place, re-run gate)" >&2
        echo "       Details: jobs-local/repository-state-gate-last.json" >&2
        echo "       No zip until all checks PASS — functional repo + NEW capability (not find-and-fix)." >&2
        echo "       Override (explicit only): TERMINUS_TASK_GENERATION_SKIP=1 ./scripts/pack_zip.sh $task_name" >&2
        return 1
      fi
    fi
    if [ "${TERMINUS_ANTI_SPAM_SKIP:-0}" != "1" ]; then
      local spam_args=(pack --task-name "$task_name")
      if [ "${TERMINUS_ANTI_SPAM_STRICT_REPO:-0}" = "1" ]; then
        spam_args+=(--strict-repo)
      fi
      if ! "$python" "$REPO_ROOT/scripts/terminus_anti_spam_auto.py" "${spam_args[@]}"; then
        echo "ERROR: Anti-spam/templated gate failed (see .cursor/rules/engines/ENGINE_2_anti_spam.mdc)" >&2
        echo "       Details: jobs-local/anti-spam-last.txt jobs-local/anti-spam-post-create-last.json" >&2
        echo "       Fix task in place until PASS — do not use skip unless user explicitly overrides." >&2
        echo "       Override (explicit only): TERMINUS_ANTI_SPAM_SKIP=1 ./scripts/pack_zip.sh $task_name" >&2
        return 1
      fi
      if ! "$python" "$REPO_ROOT/scripts/unacceptable_class_gate.py" --pack-gate --quiet --task-dir "$task_dir"; then
        echo "ERROR: Unacceptable-class gate failed — all 8 classes must PASS (zero tolerance)" >&2
        echo "       Policy: shared/unacceptable-task-classes.mdc" >&2
        echo "       Details: jobs-local/unacceptable-class-gate-last.json" >&2
        echo "       Blocked classes are not allowed — redesign, do not upload." >&2
        echo "       Override (explicit only): TERMINUS_ANTI_SPAM_SKIP=1 ./scripts/pack_zip.sh $task_name" >&2
        return 1
      fi
      if ! "$python" "$REPO_ROOT/scripts/task_uniqueness_gate.py" --pack-gate --quiet --task-dir "$task_dir"; then
        echo "ERROR: Task-uniqueness gate failed — distinct workflow/artifact/industry required" >&2
        echo "       Policy: shared/task-uniqueness-gate.mdc" >&2
        echo "       Details: jobs-local/task-uniqueness-gate-last.json" >&2
        echo "       Fix task in place — new domain/workflow/artifact, not keyword swap." >&2
        return 1
      fi
    fi
    if [ "${TERMINUS_FIRST_SUBMIT_SKIP:-0}" != "1" ]; then
      if ! "$python" "$REPO_ROOT/scripts/first_submit_pack_gate.py" --pack-gate --quiet --task-dir "$task_dir"; then
        echo "ERROR: First-submit acceptance gate failed (Phase F′ — trivial-first-upload-lock + first-submit-acceptance-gate)" >&2
        echo "       No zip file created — record PASS before pack." >&2
        echo "       Details: jobs-local/first-submit-last.txt" >&2
        echo "       Record PASS after probes:" >&2
        echo "         python3 scripts/first_submit_pack_gate.py --record --task-dir $task_dir \\" >&2
        echo "           --oracle 1.0 --nop 0.0 --probe 1=PASS --probe 3=PASS --probe 4=PASS --probe 5=PASS ..." >&2
        echo "       Override (explicit only): TERMINUS_FIRST_SUBMIT_SKIP=1 ./scripts/pack_zip.sh $task_name" >&2
        return 1
      fi
    fi
    if [ "${TERMINUS_AGENT_CALIBRATION_SKIP:-0}" != "1" ]; then
      if ! "$python" "$REPO_ROOT/scripts/preupload_agent_calibration.py" --pack-gate --task-dir "$task_dir"; then
        echo "ERROR: Agent calibration gate failed — HARD target worst ≤20% (Opus ≤20% for hard tasks)" >&2
        echo "       Policy: shared/no-easy-upload-lock.mdc (probes PASS ≠ agents fail)" >&2
        echo "       After Case 6 + local smoke:" >&2
        echo "         python3 scripts/preupload_agent_calibration.py --record --task-dir $task_dir --opus 1/5 --gpt 2/5 --post-harden" >&2
        echo "       Override (explicit only): TERMINUS_AGENT_CALIBRATION_SKIP=1 ./scripts/pack_zip.sh $task_name" >&2
        return 1
      fi
    fi
    if [ "${TERMINUS_DIFFICULTY_DESIGN_SKIP:-0}" != "1" ]; then
      if ! "$python" "$REPO_ROOT/scripts/preupload_difficulty_design_gate.py" --pack-gate --task-dir "$task_dir"; then
        echo "ERROR: Difficulty design gate failed — platform EASY surface or metadata" >&2
        echo "       Policy: shared/no-easy-upload-lock.mdc" >&2
        echo "       Override (explicit only): TERMINUS_DIFFICULTY_DESIGN_SKIP=1 ./scripts/pack_zip.sh $task_name" >&2
        return 1
      fi
    fi
    if [ "${TERMINUS_TRIVIAL_SHAPE_SKIP:-0}" != "1" ]; then
      if ! "$python" "$REPO_ROOT/scripts/preupload_trivial_shape_gate.py" --pack-gate --task-dir "$task_dir"; then
        echo "ERROR: Trivial shape gate failed — task predicts platform EASY/TRIVIAL" >&2
        echo "       Policy: shared/block-trivial-platform-acceptance.mdc" >&2
        echo "       Details: jobs-local/gates/trivial-shape-last.txt" >&2
        echo "       Fix: Case 6 depth + auto-probes PASS + agent smoke worst ≤20%" >&2
        echo "       Override (explicit only): TERMINUS_TRIVIAL_SHAPE_SKIP=1 ./scripts/pack_zip.sh $task_name" >&2
        return 1
      fi
    fi
    if [ "${TERMINUS_SUBMISSION_EXPLANATIONS_SKIP:-0}" != "1" ]; then
      if ! "$python" "$REPO_ROOT/scripts/submission_explanations_gate.py" --pack-gate --ensure --slug "$task_name"; then
        echo "ERROR: Submission explanations missing or invalid (platform upload form)" >&2
        echo "       Policy: shared/submission-explanations-gate.mdc" >&2
        echo "       Draft: python3 scripts/write_submission_explanations.py --slug $task_name --draft" >&2
        echo "       Override (explicit only): TERMINUS_SUBMISSION_EXPLANATIONS_SKIP=1 ./scripts/pack_zip.sh $task_name" >&2
        return 1
      fi
    fi
    if [ "${TERMINUS_PLATFORM_RUBRIC_SKIP:-0}" != "1" ]; then
      if ! "$python" "$REPO_ROOT/scripts/platform_rubric_gate.py" --pack-gate --slug "$task_name"; then
        echo "ERROR: Platform rubric missing or invalid (positive cumulative 10–40 per block)" >&2
        echo "       Policy: shared/platform-rubric-gate.mdc" >&2
        echo "       Write: python3 scripts/write_platform_rubric.py --slug $task_name --lines-file /tmp/rubric.txt" >&2
        echo "       Details: jobs-local/gates/platform-rubric-last.json" >&2
        echo "       Override (explicit only): TERMINUS_PLATFORM_RUBRIC_SKIP=1 ./scripts/pack_zip.sh $task_name" >&2
        return 1
      fi
    fi
    local preflight_args=(--pack-gate --quiet --task-dir "$task_dir")
    if ! "$python" "$REPO_ROOT/scripts/terminus_ci_check.py" "${preflight_args[@]}"; then
      echo "ERROR: preflight failed — CI + category + files (see jobs-local/ci-check-last.txt)" >&2
      echo "       Run: python3 scripts/terminus_ci_check.py --task-dir $task_dir" >&2
      return 1
    fi
  fi

  mkdir -p "$out_dir"
  rm -f "$out_zip"

  (
    cd "$task_dir"
    zip -r "$out_zip" . "${ZIP_EXCLUDES[@]}"
  )

  local tmp
  tmp="$(mktemp -d)"
  unzip -q "$out_zip" -d "$tmp"

  if [ "$milestone" -eq 1 ]; then
    [ -f "$tmp/task.toml" ] && [ -d "$tmp/steps" ] || {
      echo "ERROR: Bad milestone layout in $out_zip" >&2
      rm -rf "$tmp"
      return 1
    }
  else
    [ -f "$tmp/task.toml" ] && [ -f "$tmp/tests/test.sh" ] && [ -f "$tmp/environment/Dockerfile" ] || {
      echo "ERROR: Bad layout in $out_zip" >&2
      rm -rf "$tmp"
      return 1
    }
    [ -f "$tmp/tests/test_outputs.py" ] || {
      echo "ERROR: Missing tests/test_outputs.py in $out_zip (G-026)" >&2
      rm -rf "$tmp"
      return 1
    }
  fi

  if [ -d "$tmp/$task_name" ]; then
    echo "ERROR: Nested folder $task_name/ in zip" >&2
    rm -rf "$tmp"
    return 1
  fi

  if find "$tmp" -name 'rubric.md' -print -quit | grep -q .; then
    echo "ERROR: rubric.md in $out_zip" >&2
    rm -rf "$tmp"
    return 1
  fi

  if find "$tmp" -type d -name '.ruff_cache' -print -quit | grep -q .; then
    echo "ERROR: .ruff_cache directory present in $out_zip — remove before submit" >&2
    rm -rf "$tmp"
    return 1
  fi

  rm -rf "$tmp"

  if [ -z "$python" ]; then
    for cmd in python3 python; do
      if command -v "$cmd" >/dev/null 2>&1; then
        python="$cmd"
        break
      fi
    done
  fi

  if [ -n "$python" ]; then
    "$python" -c "
import zipfile, sys
z = zipfile.ZipFile(sys.argv[1])
bad = [n for n in z.namelist() if chr(92) in n]
if bad:
    print('ERROR: backslash paths:', bad[:5], file=sys.stderr)
    sys.exit(1)
" "$out_zip"
  fi

  if [ -n "$python" ]; then
    if ! "$python" "$REPO_ROOT/scripts/terminus_verify_submit.py" --task-dir "$task_dir" --zip "$out_zip"; then
      echo "ERROR: terminus_verify_submit.py failed (G-025–G-027 — task dir + zip)" >&2
      rm -f "$out_zip"
      return 1
    fi
  fi

  local bytes
  bytes="$(wc -c <"$out_zip" | tr -d ' ')"
  echo "OK   $out_zip ($bytes bytes)"

  if [ -n "$python" ]; then
    "$python" "$REPO_ROOT/scripts/terminus_anti_spam_check.py" \
      --register-pack --quiet --task-name "$task_name" || true
  fi
}

pack_all() {
  local ok=0 skip=0 fail=0

  for dir in "$REPO_ROOT/tasks"/*/; do
    [ -d "$dir" ] || continue
    local name
    name="$(basename "$dir")"
    case "$name" in
      _*) echo "SKIP $name (underscore prefix)"; skip=$((skip + 1)); continue ;;
    esac
    [ -f "$dir/task.toml" ] || { echo "SKIP $name (no task.toml)"; skip=$((skip + 1)); continue; }
    if ! is_milestone_task "$dir"; then
      if [ ! -f "$dir/tests/test.sh" ]; then
        echo "SKIP $name (no tests/test.sh)"
        skip=$((skip + 1))
        continue
      fi
    fi
    if pack_one "$name"; then
      ok=$((ok + 1))
    else
      fail=$((fail + 1))
    fi
  done
  echo "--- tasks/: ok=$ok skipped=$skip failed=$fail ---"

  local python=""
  for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
      python="$cmd"
      break
    fi
  done
  if [ -n "$python" ] && [ "${TERMINUS_ANTI_SPAM_SKIP:-0}" != "1" ]; then
    "$python" "$REPO_ROOT/scripts/terminus_anti_spam_check.py" --pack-summary || true
  fi

  [ "$fail" -eq 0 ]
}

TASK_NAME=""
MILESTONE=-1
PACK_ALL=0

while [ $# -gt 0 ]; do
  case "$1" in
    --all)          PACK_ALL=1; shift ;;
    --milestone)    MILESTONE=1; shift ;;
    --no-milestone) MILESTONE=0; shift ;;
    -h|--help)      usage ;;
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

if [ "$PACK_ALL" -eq 1 ]; then
  pack_all
  exit 0
fi

[ -n "$TASK_NAME" ] || usage
pack_one "$TASK_NAME" "$MILESTONE"
