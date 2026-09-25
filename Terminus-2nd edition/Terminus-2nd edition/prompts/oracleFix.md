# Oracle solution failed — fix guide (G-025–G-027) — LOCKED

**Hub:** `.cursor/rules/shared/WORKFLOW-MAP.mdc` · **Pack:** `./scripts/pack_zip.sh <name>`

**LOCKED:** Agents must follow this doc (and `.cursor/rules/revise/oracle-fix-g025-g027.mdc`) for **every** **Oracle solution failed** / platform oracle **0** case before resubmit.

Use this doc when platform difficulty-check shows **Oracle solution failed**, oracle reward **0** with **no agent runs**, or local oracle passes but platform fails.

**Related:** `scripts/terminus_verify_submit.py` · registry **G-025–G-027** in `.cursor/rules/revise/platform-hardness-guards.mdc` · full rule `.cursor/rules/revise/oracle-fix-g025-g027.mdc` · verifier `.cursor/rules/shared/runtime-verifier.mdc` · workflow `@REVISE RULES`

---

## Why local can pass but platform fails

Platform oracle runs with **`allow_internet = false`**. Local Docker with **network enabled** hides:

1. **`solve.sh` downloads or compiles** (Maven, Hex, npm, …) — **G-025**
2. **Submission zip missing `tests/test_outputs.py`** — **G-026**
3. **Zip paths use backslashes** (`environment\Dockerfile`) — **G-027**

---

## G-025 — Oracle `solve.sh` must be offline

### Evidence (2026-06)

| Task | Failure |
|------|---------|
| `tasks/scala-vault-rotation-secrets-audit-repair` | `sbt assembly` → `UnknownHostException` for `repo1.maven.org` |
| `tasks/elixir-rollout-admission-coordinator-repair` | `mix local.hex` / `mix deps.get` at oracle time; stale beams after copy-only fix |

### Forbidden in `solution/solve.sh` / `solveN.sh`

| Pattern | Why |
|---------|-----|
| `sbt`, `sbt assembly`, `./gradlew`, `mvn …`, `cargo fetch` / `cargo build` without offline cache | Downloads toolchains or deps |
| `mix local.hex`, `mix local.rebar`, `mix deps.get`, `mix deps.compile` without `MIX_OFFLINE=1` + deps in image | Hits Hex / `builds.hex.pm` |
| `npm install`, `pip install`, `curl`, `wget`, `apt-get install` | Same as verifier runtime install blockers |
| Copy fixed sources **without** offline recompile when runtime uses compiled artifacts | Stale broken beams/JARs (Elixir partial pass) |

### Required patterns by stack

| Stack | Oracle must |
|-------|-------------|
| **Scala / JVM** | Ship **`solution/fixed/*.jar`** (or image-built JAR); `install` to `/app/lib/` — **no `sbt`/`gradle`/`mvn` in `solve.sh`** |
| **Elixir** | `export MIX_OFFLINE=1`; copy `fixed/*.ex` → **`mix compile --force`** only (deps/Hex in **Dockerfile** build) |
| **Rust** | Prebuilt `/app/bin/*` in image; prefer copy prebuilt binary from `solution/fixed/` — no network `cargo fetch` |
| **Go** | `go build -mod=vendor` using image `/app/vendor` — never `go mod download` in `solve.sh` |
| **Go CGO (sqlite3)** | `export PATH="/usr/local/go/bin:/app/bin:${PATH}"` + `export CGO_ENABLED=1` in **`solve.sh` and `build.sh`**; Dockerfile copies `/usr/local/go` + **build-essential** to runtime; image builds `vendor` in builder |

**Rule:** After copying fixed sources to a compiled stack, refresh artifacts (recompile or replace JAR/beam/binary). Copying `.ex`/`.scala` alone is **not** enough if `/app/bin` or `_build` still holds broken env binaries.

### Go CGO oracle failure — `go: command not found` (G-025)

**Evidence (2026-06):** `tasks/ev-charger-loadshed-session-auditor` — platform **Oracle solution failed**; agent log: `/app/scripts/build.sh: go: command not found`. Local oracle can pass when Docker `ENV PATH` is set but Harbor oracle **`solve.sh`** runs without inheriting it reliably.

**Fix (both files):**

```bash
export PATH="/usr/local/go/bin:/app/bin:${PATH}"
export CGO_ENABLED=1
```

Add `test -x /app/bin/<binary>` at end of `solve.sh` to fail fast before verifier runs.

### Audit

```bash
cd tasks/<task-name>
rg -n 'sbt |sbt$|mix local\.|mix deps\.|gradle |mvn |cargo fetch|npm install|pip install|curl |wget |apt-get install' \
  solution/ || true
python scripts/terminus_verify_submit.py --task-dir .
```

**High blocker:** any `rg` hit in `solution/` unless the line is a comment documenting a forbidden pattern.

### Verify oracle offline

```bash
# Docker: no network (catches G-025 locally)
docker run --rm --network none -v "$(pwd)/solution:/solution:ro" <image> bash /solution/solve.sh

# Platform-equivalent when WSL available
stb harbor run -a oracle -p . --debug --force-build
```

---

## G-026 — Submission zip must include `tests/test_outputs.py`

### Evidence (2026-06)

`tasks/romance-emotion-escalation-audit-cli` — uploaded zip had `tests/test.sh` + helpers only; platform pytest: **`file or directory not found: /tests/test_outputs.py`** → oracle **0**. Live tree had the file; incomplete zip omitted it.

### Required (non-milestone)

- Archive root must include **`tests/test_outputs.py`** at path `tests/test_outputs.py`.
- Do **not** assume `tests/test.sh` alone is sufficient.

```bash
unzip -l tasksubmit/<task-name>.zip | rg 'tests/test_outputs\.py'
python scripts/terminus_verify_submit.py --zip tasksubmit/<task-name>.zip
```

**High blocker:** non-milestone zip without `tests/test_outputs.py`.

---

## G-027 — No backslash paths in zip entries

### Evidence (2026-06)

`tasks/elixir-rollout-admission-coordinator-repair` — zip listed `environment\Dockerfile`; CodeBuild: **`environment: Directory does not exist`**.

### Forbidden

- Windows `Compress-Archive` from **outside** the task folder
- Any zip entry containing **`\`**

### Required

- **`./scripts/pack_zip.sh <name>`** from repo root (never manual `zip -r` for upload)
- **`./scripts/pack_zip.sh <name>`** (Mac/Linux) or **`scripts/pack_zip.ps1`** (Windows)
- Or `python scripts/terminus_verify_submit.py --zip …`

```bash
python -c "import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); bad=[n for n in z.namelist() if chr(92) in n]; print('FAIL backslash:', bad) if bad else print('OK paths')" tasksubmit/<task>.zip
```

**High blocker:** any backslash in `ZipFile.namelist()` output.

---

## Verify before zip (mandatory)

Run **both** when claiming ready to submit:

```bash
python scripts/terminus_verify_submit.py --task-dir tasks/<task-name>
python scripts/terminus_verify_submit.py --task-dir tasks/<task-name> --zip tasksubmit/<task-name>.zip
```

On Windows use `python` if `python3` is not on PATH.

The script checks:

- G-025: forbidden patterns under `solution/`
- G-026: `tests/test_outputs.py` in zip (non-milestone)
- G-027: no `\` in zip entry names
- Flat archive root (`environment/Dockerfile`, `tests/test.sh` at top level)

---

## Pack submission zip (flat root)

```bash
./scripts/pack_zip.sh <task-name>
```

**Also verify:**

```bash
file tasksubmit/<task-name>.zip    # must say: Zip archive data
unzip -t tasksubmit/<task-name>.zip
```

Do **not** use `tar -a -cf …zip` (POSIX tar, not Zip). Do **not** use `Compress-Archive` from outside the task folder.

---

## Pre-submit checklist (oracle + zip)

- [ ] `solution/solve.sh`: no runtime network/compile (**G-025**); Elixir `MIX_OFFLINE=1` + `mix compile --force` after copy; JVM prebuilt JAR in `solution/fixed/`
- [ ] Zip includes `tests/test_outputs.py` (**G-026**); no backslash paths (**G-027**)
- [ ] `terminus_verify_submit.py` pass on task dir **and** zip
- [ ] Oracle reward **1.0**, NOP **0.0** (WSL `stb harbor` when available)
- [ ] `file *.zip` → **Zip archive data**; flat root after unzip

---

## Registry (one-line guards)

| ID | Guard |
|----|--------|
| **G-025** | Oracle `solve.sh`: **no** `sbt`/`mix deps.get`/network; JVM **prebuilt JAR**; Elixir **`MIX_OFFLINE=1` + `mix compile --force`** |
| **G-026** | Non-milestone zip **must** include `tests/test_outputs.py` |
| **G-027** | No backslashes in zip entries; pack from inside `tasks/<name>/` |

Full evidence rows: `.cursor/rules/revise/platform-hardness-guards.mdc` § Proven registry.

---

## Revision prompt (paste to agent)

```
Platform: Oracle solution failed. Follow oracleFix.md (G-025–G-027).

1. Inspect solution/solve.sh — remove sbt/mix deps.get/network; apply stack table in oracleFix.md.
2. Repack tasksubmit zip — include tests/test_outputs.py; forward-slash paths only.
3. Run: python scripts/terminus_verify_submit.py --task-dir tasks/<name> --zip tasksubmit/<name>.zip
4. Re-oracle and NOP before resubmit.
```

Also usable via **`reviewer.md`** when pasting platform feedback.
