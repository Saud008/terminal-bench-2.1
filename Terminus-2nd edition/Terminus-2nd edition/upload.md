# Terminus task upload (Edition 2)

CodeBuild copies `$CODEBUILD_SRC_DIR/*` into `~/tasks/tbench-task/`. The **zip archive root** must already be the task — not a folder named after the task.

## Correct layout after unzip

```text
instruction.md
task.toml
environment/
  Dockerfile
  ...
tests/
  test.sh
  test_outputs.py
solution/
  solve.sh
```

## Wrong layouts (static check failures)

```text
deterministic_segment_seal_barrier_replay/   ← nested task folder
  instruction.md
  environment/
  tests/test.sh

tasksubmit/deterministic_segment_seal_barrier_replay.zip   ← zip inside zip

tasks/   ← zipping the parent directory
```

Typical CodeBuild errors when the layout is wrong:

- `environment: Directory does not exist`
- `tests/test.sh: File does not exist`

### Milestone tasks (Harbor multi-step)

```text
task.toml
environment/
steps/milestone_1/instruction.md
steps/milestone_1/tests/test.sh
steps/milestone_1/solution/solve.sh
steps/milestone_2/...
steps/milestone_3/...
```

Do **not** ship root `milestone_N.md`, root `tests/`, or root `solution/` for milestone tasks — AutoEval / Harbor quality check expects `steps/<name>/`.

### Windows `Compress-Archive` trap (backslashes)

PowerShell `Compress-Archive` stores zip entry names with **backslashes** (`environment\Dockerfile`, `tests\test.sh`). On Linux CodeBuild those often extract as **files with `\` in the name**, not real directories.

Symptom: `milestone_1.md` passes (no `\` in path) but `environment/` and `tests/test.sh` fail.

**Fix:** pack with **`tar`** or **`pack_zip.ps1`** only — never `Compress-Archive` for upload.

## Pack from `tasks/<task-name>/` (canonical source)

Always create the zip **from inside** the task directory so paths are relative to the archive root.

### Mac / Linux (recommended)

From repo root:

```bash
./scripts/pack_zip.sh <task-name>
# milestone: ./scripts/pack_zip.sh <task-name> --milestone
```

Excludes **`rubric.md`**, verifies flat root and forward-slash paths (G-027).

### Pack all tasks

```bash
./scripts/pack-all-upload-zips.sh
```

**Do not** pack by hand. Always use `scripts/pack_zip.sh` or `scripts/pack_zip.ps1` — they enforce G-026 (`tests/test_outputs.py`), G-027 (no backslashes), flat root, and `rubric.md` exclusion.

### Windows (recommended)

**Do not** right-click → Compress the task folder from Explorer or run `Compress-Archive -Path tasks\<name>` from the repo root — that nests the folder name and fails CI.

**Option A — `tar` from inside the task folder:**

```powershell
cd tasks\<task-name>
tar -a -cf ..\..\tasksubmit\<task-name>.zip `
  --exclude=.pytest_cache --exclude=.ruff_cache --exclude=output --exclude=jobs `
  --exclude=**/__pycache__ `
  instruction.md task.toml environment tests solution
```

Milestone task:

```powershell
cd tasks\<task-name>
tar -a -cf ..\..\tasksubmit\<task-name>.zip `
  --exclude=.pytest_cache --exclude=.ruff_cache --exclude=output --exclude=jobs `
  --exclude=**/__pycache__ `
  task.toml environment steps
```

**Option B — `scripts/pack_zip.ps1` from repo root (recommended):**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\pack_zip.ps1 -TaskName <task-name>
```

Writes `tasksubmit/<task-name>.zip`. Uses WSL `zip` when available (forward-slash paths). **Excludes `rubric.md`** always; fails if rubric or backslash paths end up in the zip.

Milestone: `-Milestone`.

## Verify before upload

```powershell
$z = (Resolve-Path "tasksubmit\<task-name>.zip").Path
$v = Join-Path $env:TEMP "zip_check"
Remove-Item $v -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $v | Out-Null
tar -xf $z -C $v
Test-Path "$v\environment\Dockerfile"   # must be True
Test-Path "$v\tests\test.sh"            # must be True
Test-Path "$v\<task-name>\environment"  # must be False (no nested root)

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($z)
($zip.Entries | Where-Object { $_.FullName -match '\\' }).Count  # must be 0
$zip.Dispose()
```

Prefer `tar -xf` over `Expand-Archive` for verification; `Expand-Archive` can mask the backslash-path bug on Windows.

## Exclude from the zip

`.pytest_cache/`, `.ruff_cache/`, `output/`, `jobs/`, `__pycache__/`, `*.pyc`, **`rubric.md`** (never pack — platform rubric is separate)

## `task.toml` (Harbor static checks)

Every zip must include in `task.toml`:

```toml
[agent]
timeout_sec = 1800

[verifier]
timeout_sec = 900

[environment]
allow_internet = false
build_timeout_sec = 900.0
cpus = 2
memory_mb = 4096
storage_mb = 10240
workdir = "/app"
```

Use `build_timeout_sec = 600.0` or `900.0` only (not both). Prefer `900.0` for C++/Qt/JVM image builds.

**Milestone tasks** (`number_of_milestones` > 0) still need root `[agent]` and `[verifier]` for CodeBuild, plus `[[steps]]` per-milestone timeouts, `steps/milestone_N/instruction.md`, `steps/milestone_N/tests/test.sh`, `steps/milestone_N/tests/test_mN.py`, and `steps/milestone_N/solution/solveN.sh`. Without root timeouts you get:

- `Missing required field: .agent.timeout_sec`
- `Missing required field: .verifier.timeout_sec`

## This repo (LOCKED)

| Live tree | Upload zip |
|-----------|------------|
| `tasks/<task-name>/` | `tasksubmit/<task-name>.zip` |

- No `rubric.md` in any zip (repo policy)
- `task.toml` must include `[environment] allow_internet = false` and root `[agent]` / `[verifier]` timeouts
- **`[metadata].subcategories`** — **always `[]`** (empty) in this repo; do not assign Harbor subcategory labels

See also: `upload_readme`, `.cursor/rules/zip/ZIP-RULES.mdc`, `.cursor/rules/shared/repo-workflow.mdc`.

## Platform submission form (new fields)

Fill these on the project website at upload — not stored in the zip.

| Field | When / how |
|-------|------------|
| **Approved canonical base image?** | **Yes** if `environment/Dockerfile` first `FROM` matches the canonical image for your stack (`.cursor/rules/shared/platform-preferences.mdc` §6 or website list when published). **No** + justification if you must use a different base. `@sha256:` digest pinning is required either way. |
| **Task Inspiration ID** | Copy from the inspiration gallery (ID under the title) when your task is based on a website inspiration. Leave blank if original (not inspiration-based). |

Platform eval checks canonical base usage; non-canonical without justification fails review.