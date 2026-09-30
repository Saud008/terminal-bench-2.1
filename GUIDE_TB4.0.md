# Caudal Terminal Bench 4.0 — contributor guide (as issued)

Source: the pool's TB 4.0 guide pages, pasted verbatim in content. Authority: `MASTER_CHECKLIST_TB4.0.txt` wins on any conflict; this guide sits directly below it.

---

## Getting Started

### What is Terminal Bench 4.0?

Terminal Bench 4.0 is a benchmark for evaluating AI coding agents on real-world engineering tasks. Your job is to create tasks that challenge today's best models — tasks that require genuine engineering reasoning, multi-step problem solving, and practical skills.

Terminal Bench 4.0 tests:

- Multi-step reasoning — tasks require chaining multiple commands, with real investigation and recovery in between
- Environment interaction — agents work in real Docker containers, with the verifier running in a separate container of its own
- Practical skills — real debugging, configuration, and development tasks, not trivia

Note: While this project is not affiliated with the official Terminal-Bench project, we closely follow its style.

### Your Role as a Coding Expert

- Design tasks that challenge frontier AI models
- Write oracle solutions that demonstrate correct completion
- Write a verifier that checks completion deterministically, from its own separate container
- Write a task-specific rubric.txt and a plain-language difficulty_explanation
- Iterate on feedback from automated checks and peer review

Every task runs against GPT-5.6 (xhigh reasoning effort) five times as part of its evidence package. Terminal Bench 4.0 does not turn that into a label: there is no difficulty field, no tier name, and no pass-rate or percentage anywhere in a delivered task.

Difficulty is prose, not a tag: `[metadata].difficulty_explanation` is where you describe what makes the task genuinely hard, in plain language — never a measured rate, a run count, or a tier word. Reviewers judge whether that explanation holds up against the evidence; they don't assign a category from it.

Each task undergoes a rigorous review:

- Automated CI checks — technical requirements (structure, pinning, reserved paths)
- LLM-as-Judge (LLMaJ) — quality evaluation using GPT-5.6
- Peer / QC review — human verification against the QC Rubrics
- Agent evaluation — run against GPT-5.6, xhigh reasoning effort, five runs

### Quick Start Guide

Prerequisites: Docker installed and running; Python 3.12 or 3.13; a terminal; roughly 10 GB free disk.

The Path:

1. Pick exactly one category and subcategory from the taxonomy that matches domain knowledge you actually have.
2. Draft the contract before writing code: output paths, formats, edge cases. This becomes instruction.md.
3. Build environment/ from a canonical base image, with tmux and asciinema preinstalled.
4. Write solution/solve.sh — a deterministic oracle that genuinely derives the answer.
5. Write tests/ — test.sh, test_outputs.py, test_manifest.json — running in its own verifier container.
6. Run Oracle and NOP locally; confirm reward is 1.0 and 0.0 respectively on every test.
7. Run the five-attempt GPT-5.6 batch and read the trial analysis before trusting the result.
8. Write rubric.txt, confirming it never references tests, files, or the Oracle/NOP runs.
9. Walk the delivery checklist, package the bundle, and submit for QC review.

Skeleton:

```text
task-name/
├─ task.toml
├─ instruction.md
├─ rubric.txt
├─ environment/
│   └─ Dockerfile
├─ solution/
│   └─ solve.sh
└─ tests/
    ├─ Dockerfile
    ├─ test.sh
    ├─ test_outputs.py
    └─ test_manifest.json
```

Troubleshooting: agent runs failing across the board with no useful signal is almost always a missing tmux or asciinema in the environment image. A verifier that "sees nothing" is almost always `artifacts` nested under `[verifier]` instead of the top level of task.toml.

### What's New in Terminal Bench 4.0

| Topic | TB 4.0 |
|---|---|
| allow_internet | Replaced by `network_mode = "public"` or `"no-network"` |
| Verifier location | Builds and runs in its own separate container (`environment_mode = "separate"`), not inside the agent's |
| Milestones | Removed entirely — no number_of_milestones or milestone layout |
| Agent/verifier timeout | Fixed at 28800 seconds on every task, not a tunable range |
| Pass rates above ~80% | An Easy tier exists deliberately — no longer an automatic rejection, though 100% is still never accepted as-is |
| Category taxonomy | 7 domains / 29 subdomains, exactly one category + one subcategory required |
| Rubric | rubric.txt hand-authored by the contributor and shipped in the bundle |
| Anti-cheat | NC-01–NC-14 negative-control catalog, mandatory for NC-01–06 |
| Solution/verifier evidence | Oracle ×3 + NOP ×2 full-suite evidence, plus a five-attempt GPT-5.6 anti-saturation batch |

Unchanged: no GPU is required or supported. GPU-adjacent work stays in scope via CPU-simulated kernels or compile-only verification.

---

## What Makes a Good Task

### Four Tenets

- **Novel** — not a variation on any prior benchmark-edition task. Reskins (same computation, different cover story) are not novelty.
- **Multi-Step** — a credible expert solution needs at least five terminal commands plus real intermediate reasoning: investigation, branching, recovery.
- **Testable** — fully specified, deterministic final-state verification. No mid-run human input.
- **Standalone** — runs without any external dependency beyond what's baked into the images at build time.

### Where Difficulty Comes From

Difficulty comes from how much has to be true simultaneously for a result to be correct — not from obscurity or sheer volume of work.

Works: requiring the agent to infer a contract from domain evidence rather than being told it; demanding a native, structurally valid artifact rather than something that merely looks right; adding a second correctness axis that interacts with the first; verifying against hidden variations that test understanding, not memorization of one example.

Doesn't work: piling on unrelated independent requirements (length, not difficulty); ambiguity or under-specification; obscure trivia with no reasoning behind it; anything that makes runs non-deterministic.

### One Coherent Incident

A task's defects should trace to one nameable root cause. More than roughly three unrelated planted defects bundled under a thin shared narrative reads as a "bug zoo." If instruction.md's flavor text describes only one of several planted bugs, that's a tell you've drifted into one.

---

## Task Components and Requirements

```text
task-name/
├─ task.toml           the manifest
├─ instruction.md      what, never how
├─ rubric.txt          agent-conduct criteria, authored by you
├─ environment/        agent-facing, self-contained
│   └─ Dockerfile
├─ solution/           the oracle
│   └─ solve.sh
└─ tests/              the verifier, its own container
    ├─ Dockerfile
    ├─ test.sh
    ├─ test_outputs.py
    └─ test_manifest.json
```

Silent-drop gotcha: top-level `artifacts = [...]` must stay at the top level of task.toml. Nesting it under `[verifier]` does not raise an error — it's silently dropped and the verifier receives nothing.

### task.toml fields

| Field | Req | Notes |
|---|---|---|
| artifacts | ✓ | Top level only. List of every path the verifier needs. |
| category | ✓ | Exactly one, Title Case, from the 7-domain / 29-subdomain taxonomy. |
| subcategory | ✓ | Exactly one, Title Case, matching the same taxonomy. |
| languages | ✓ | Primary implementation language(s) actually exercised — not domain tooling, not "python" just because the test suite is pytest. |
| tags | ✓ | 3–6, specific to this task. |
| expert_time_estimate_hours | ✓ | Realistic estimate for an expert. |
| write-up fields | ✓ | difficulty_explanation, solution_explanation, verification_explanation, relevant_experience — all four, substantive. |
| is_multi_container | optional | Set only when the task genuinely needs more than one service. |
| [verifier] | ✓ | environment_mode = "separate", timeout_sec = 28800. |
| [agent] | ✓ | timeout_sec = 28800 — this program's deliberate default on every task. |
| [environment] | ✓ | network_mode, cpus, memory_mb, storage_mb. |

### Constraints

- Compute envelope: ~2 CPU cores, ~8 GB memory, ~10 GB storage — no GPU, ever.
- Network: `network_mode = "public"` by default; `"no-network"` only when public internet would let the agent skip the actual work.
- Canary strings: banned everywhere — instruction, environment, solution, tests, metadata, trajectories.
- Folder naming: kebab-case, descriptive — never task1 or test.
- Task name in instructions: must never appear inside instruction.md's body.
- Dependency pinning: digest-pin every FROM/image:; exact-pin language packages; never version-pin apt packages.
- Supported primary languages: Python, C, C++, JavaScript, TypeScript, Java, Go, Rust, C#. Multi-language tasks are welcome.

```toml
artifacts = ["/app/output.json"]      # top-level ONLY
name = "your-task-name"

[metadata]
category = "Software"
subcategory = "Databases"
tags = ["python", "wal", "recovery", "concurrency"]
languages = ["python"]
difficulty_explanation = "..."        # plain-language prose only - no tier, number, or pass rate anywhere

[verifier]
timeout_sec = 28800
environment_mode = "separate"

[agent]
timeout_sec = 28800

[environment]
network_mode = "public"
cpus = 2
memory_mb = 8192
storage_mb = 10240
```

### Task Taxonomy (7 domains, 29 subdomains, Title Case, exact match)

| Domain | # | Subdomains |
|---|---|---|
| Science | 7 | Biology, Chemistry, Physics, Earth, Robotics, Math, Linguistics |
| Software | 5 | Algorithms, Systems, Databases, Data engineering, Frontend |
| ML | 4 | Training, Inference, Evaluation, Kernels |
| Operations | 6 | Finance, Logistics, Supply chain, Claims, Compliance, Marketing |
| Security | 3 | Cryptography, Forensics, AppSec |
| Hardware | 2 | CAD, RTL |
| Media | 2 | Music, Design |

Pick the domain the task actually lives in, then the subdomain describing the specific work. The most common mistake is defaulting to Software because the task involves writing code. Ask: what does the agent have to understand to get this right? A task that debugs a training loop is ML / Training, not Software / Systems; parsing mass spectra to infer a molecular structure is Science / Chemistry, not Software / Algorithms. If a task spans two domains, choose the one whose domain knowledge the agent cannot succeed without.

ML / Kernels without a GPU: CPU-simulated kernels checked for numerical correctness against a CPU reference, or compile-only verification (compiles and passes static checks without executing on device).

### Submission Diversity

Novelty is checked against the whole corpus, including prior benchmark editions. A reskin is caught by similarity comparison. Before you build, search for: the task's own name or core concept; a key error message or identifier the task would produce; the likely upstream algorithm or library the domain points to. Record what you checked and why this task is genuinely different — a human judgment call reviewers document. Spread submissions across a few categories and subcategories.

---

## Rubrics (rubric.txt)

| Artifact | Grades |
|---|---|
| tests/ | Whether the final artifact is correct |
| rubric.txt | How the agent behaved while attempting the task — task-specific, authored by you |
| QC Rubrics | The task-agnostic bar reviewers audit every bundle against |

Format rules:

- Every line starts with the literal word "Agent" and ends with ", ±N"
- Magnitudes only ±1, ±2, ±3, ±5 — 4 is never valid
- Positive scores carry an explicit +; a bare 3 is invalid
- At least one negative criterion
- Cumulative positive score sums to 10–40
- Criteria phrased positively about behavior
- Never mentions pytest, tests/ results, file existence, or Oracle/NOP runs

```text
Agent identifies the root cause before modifying the WAL replay logic, +5
Agent restores durability under a simulated crash mid-write, +5
Agent preserves existing passing behavior for non-crash recovery paths, +3
Agent hardcodes a recovery offset instead of deriving it from the log header, -5
Agent disables or skips crash-injection during its own verification, -3
```

---

## Instruction Prompt Styling

Seven principles: Concise (~2 short paragraphs or up to 20 bullets as a guide; more room when the problem's complexity needs it); Well-specified; Interesting; No answers, no hints (what, never how); Unique; Absolute paths only; No canary strings.

Voice: plain human tone over "You are an expert programmer..." framing. Minimal markdown, no emojis, no decorative unicode or em dashes as filler. Vary style task to task. Prompts are screened for AI-generated text.

Five ways instructions leak the answer:

1. A step-by-step walkthrough with solution-value constants (e.g. "set SO_RCVBUF to 262144 bytes")
2. A "Detection Guidance" section describing exactly what to look for
3. Markdown so heavy the prompt reads like API documentation
4. Function signatures or build recipes specified so exactly there's nothing left to design
5. Bold text spotlighting the one number or field that matters

Environment docs aren't a length loophole: spec files under environment/ define what (schemas, protocols, contracts), never step-by-step how. Moving instruction content into an environment doc to shorten instruction.md is a high-severity finding.

---

## Difficulty Guidelines

No difficulty field, tier, or tag anywhere. No tier name, percentage, or pass-count in task.toml, instruction.md, or any other delivered file. `difficulty_explanation` is the one place difficulty is discussed: plain-language prose about what makes the task conceptually hard — never a measured rate, run count, or tier word.

Judging the evidence: reviewers read the five GPT-5.6 runs for evidence quality. A failure only counts as genuine difficulty when it comes from the actual challenge — not unclear instructions, an environment defect, a flaky test, a content-policy refusal, or the agent running out of time. A run that fails for the wrong reason is a bug to fix.

### Bad example tasks

- Instruction: step-by-step walkthrough with solution constants; "Detection Guidance"; API-doc markdown; exact signatures/build recipes; bold spotlighting the key number.
- Environment: gibberish names where decoding the name is the task; comments naming the defect (`// TODO: planted bug for the grader`); a "bug zoo" (four or more unrelated defects under one thin narrative).
- Oracle / verifier: a verifier function that maps inputs straight to the expected artifact (if deleting solution/ wouldn't change whether the test can compute the answer, the test is doing the solving); format-only checks; any latency or throughput assertion (banned).

---

## Creating a Task

1. Rename the folder to a descriptive kebab-case slug.
2. Fill task.toml's required fields as a first pass; revisit the write-ups (especially difficulty_explanation) once the task is built.
3. Build the environment and get the agent container running by hand before writing a single test.
4. Write the oracle end to end, confirming it produces the intended artifact.
5. Write the verifier against the oracle's output, then confirm NOP fails everything.

Multi-container: use docker-compose.yaml and set `[metadata].is_multi_container = true` only when genuinely needed. Setting it on a single-container task, or omitting it on a real multi-container one, are both flagged.

### Docker Environment

- tmux and asciinema preinstalled — missing them is the #1 cause of silent all-fail runs.
- Reserved paths the agent Dockerfile must never create, copy to, chown, or chmod: /tests, /solution, /oracle, /logs/verifier, /logs/artifacts.
- No AI-scaffolding filenames (CLAUDE.md, AGENTS.md, skills.md, .cursor/, .aider/) unless the task is about that tooling.
- No privileged mode: no --privileged, no SYS_ADMIN/NET_ADMIN, no /var/run/docker.sock mount.
- Named volumes only in compose files — never a host bind mount.
- Portability: no FROM --platform=..., no silent amd64-only artifacts, no -march=native without a portable fallback.

### Dockerfile Best Practices

Blocking automatically: every FROM digest-pinned; final runtime base canonical or credibly justified; build context ≤100 MiB total, no single file >50 MiB.

| Base | Canonical reference |
|---|---|
| Python | python:3.13-slim-bookworm@sha256:01f42367… (covers 3.10–3.13) |
| Node.js | node:22-bookworm-slim@sha256:f3a68cf4… (covers 18/20/22/24) |
| Go | golang:1.24-bookworm@sha256:1a6d4452… (covers 1.21–1.26) |
| Rust | rust:1.85-slim@sha256:9f841bbe… (covers 1.75–1.95) |
| Java (JDK) | eclipse-temurin:21-jdk-jammy@sha256:25d12765… |
| C/C++ (GCC) | gcc:13-bookworm@sha256:930f2ebe… (covers 12–15) |
| Ruby | ruby:3.3-slim-bookworm@sha256:e76733e9… |
| Debian | debian:bookworm-slim@sha256:4724b8cc… |
| Ubuntu | ubuntu:24.04@sha256:0d39fcc8… |

Non-canonical bases can pass with a credible, specific justification comment — rejected outright if the justification matches an existing canonical entry.

Build hygiene: layers least-to-most volatile; one apt transaction per stage, `--no-install-recommends`, clean `/var/lib/apt/lists/*` in the same layer, never version-pin apt packages; multi-stage builds for compiled languages; files as real files, not heredocs or opaque archives; `COPY --chmod=/--chown=` narrowly, never `chmod -R`/`chown -R` on /app; ship a .dockerignore for any non-trivial environment.

### Writing the Oracle Solution

- Deterministic and human-written, with only minimal LLM syntax assistance
- Demonstrates the actual command sequence an expert would run — not just the final answer
- A minimal, targeted diff scoped exactly to the task's own planted defects — never "fixing" already-correct code
- No dead code or commented-out branches that reveal the fix
- No generator/meta commentary
- Matches instruction.md's literal wording on every case, not just the tested ones

### Writing Tests

The verifier builds from tests/Dockerfile and runs in its own container, which the agent cannot see or reach. It receives only the paths listed in top-level `artifacts`. Parent directories for every declared artifact path must already exist in the verifier image.

```bash
#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
python -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
rc=$?
if [ "$rc" -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
exit 0
```

No `set -e` (a failing pytest must not skip the reward write), and `exit 0` always (the harness reads reward.txt, not the exit code).

- Legitimate: running the agent's own binary and grading its output; golden fixtures/hashes; spec-derived invariants; sealed held-out ground truth; perturbation/holdout re-runs.
- Banned: a function in tests/ that maps inputs straight to the expected artifact; hardcoding a value the instructions say the agent must read from a config file.
- Hard bans: no wall-clock latency or throughput assertions anywhere; deterministic score thresholds fixed before model trials, from the public objective and a realistic baseline, never within ~5% of Oracle without sign-off; oracle and agent receive byte-identical verifier logic — no /oracle or identity branching.

### Oracle Agent

Reference solution run as an agent. Reward 1.0 on every named manifest test, zero flakiness. Evidence: three independent full-suite Oracle runs, all passing every test.

### NOP Agent

Does nothing and returns immediately. 0% is expected; if NOP passes, the task or verifier is broken. Evidence: two independent full-suite NOP runs; every manifest-declared test fails on both. NOP is not anti-cheat proof — that's what Negative Controls are for.

### Negative Controls

NC-01 through NC-06 are mandatory on every task and must fail through their own named assertion. NC-07–14 apply when the described trigger exists.

| ID | Control |
|---|---|
| NC-01 | Empty / no-op submission — mandatory |
| NC-02 | Format-only fake, no real content — mandatory |
| NC-03 | Hard-coded public/example answer — mandatory |
| NC-04 | Self-reported metric, no underlying work — mandatory |
| NC-05 | One declared artifact missing — mandatory |
| NC-06 | Fake reward/CTRF written from the agent side — mandatory |
| NC-07 | Naive/textbook baseline that misses the crux — when an obvious baseline exists |
| NC-08 | Primary metric passes while a second stated requirement is violated |
| NC-09 | Correct value printed but not persisted |
| NC-10 | Visible-size / first-N / sorted-input / boundary-only shortcut |
| NC-11 | Tamper with or replace a protected input/baseline |
| NC-12 | PATH shim, shadow module, or wrapper always returning success |
| NC-13 | Smallest-scale-only / warm-cache-only implementation |
| NC-14 | Fits public examples exactly, fails an unseen/metamorphic case |

A reward of 0 arriving through an unplanned, different test is a fail of that control, not a pass. When a trigger doesn't apply, it needs a specific, credible stated reason, not silence.

### Testing Agent Performance

Five GPT-5.6 runs, xhigh, captured under trajectories/run-01..run-05. No difficulty tag results. Raw pass/fail is not enough: every trial needs full causal classification before it counts toward the denominator — genuine capability failure, spec gap, refusal, infrastructure fault, reward hack, or missing evidence. Refusals, infra failures, spec gaps, and missing evidence are excluded from the defensible denominator and need repair or a full replacement round — never a silent discard.

---

## CI, LLMaJ, Agent Review

A CI failure names the check, not always the reason — reproduce locally against the files on disk. Apt packages must stay unpinned (a pinning failure is usually a language package). A task.toml structure failure is usually a field nested one level too deep (most often `artifacts` under `[verifier]`). Passing CI is necessary, not sufficient.

CI checks: manifest & metadata (required fields, verifier "separate", timeout, folder name); instructions (absolute paths, every referenced file described, human-authored screening); environment & Dockerfile (pinned images and language packages, unpinned apt, no platform pinning, no host bind mounts); verifier & tests (tests/ and solution/ absent from the agent image, verifier tooling baked and pinned, CTRF reporting present, no trial-time network fetches).

LLMaJ (GPT-5.6, informational): behavior_in_task_description; behavior_in_tests; informative_test_docstrings; anti_cheating_measures; structured_data_schema; hardcoded_solution; file_reference_mentioned.

Agent Review: automated static analysis with Critical / Warning / Suggestion findings, ending in Ready to use / Needs fixes / Requires revision. Informational, not a gate.

---

## Review Guidelines

| Severity | Meaning |
|---|---|
| Blocker | A correct solution could score 0, a wrong or empty solution could score above 0, an expert reader would flag it on inspection, or a real test passes under NOP |
| Major | A real quality defect that compounds with others or misrepresents the task |
| Minor | Polish — smaller in scope, but still a real, verified defect |

A task ships only when every finding is resolved — zero Blocker, zero Major, zero Minor. Don't send back: an unconfirmed task.toml "structure" complaint (CI already ran it), or instruction length alone past ~20 bullets.

### Reviewer Checklist

- Instruction: absolute paths only (Blocker); no hints/stepwise/Detection Guidance (Blocker); task name not in body (Major).
- Environment: reserved paths untouched (Blocker); digest-pinned canonical or justified base (Blocker); tmux and asciinema preinstalled (Blocker).
- Oracle: reward 1.0 on every test, all three runs (Blocker); minimal targeted diff (Major).
- Verifiers: no wall-clock assertions (Blocker); oracle/agent identical logic (Blocker); semantic correctness, not format-only (Blocker).
- Rubric: format compliance (Major); magnitudes ±1/±2/±3/±5 and positive sum 10–40 (Major).
- Metadata: taxonomy exact match (Major); no edition-3 residue or PII — no allow_internet, milestone fields, or real local paths (Blocker); no difficulty tag anywhere (Blocker).

### Common Errors

- Tests: brittle exact-string matching where the contract never fixed the form — check semantic correctness after normalization.
- Oracle: hardcoded answer, unseeded randomness, unsorted `ls` — derive deterministically.
- Environment: missing tmux/asciinema, trial-time package installs — bake everything at build time.
- Leakage: exposed test logic, answers reachable via git history — clean history, tests/ and solution/ absent from the agent image.
- Difficulty: too easy (one obvious command, NOP passes); unfairly hard (ambiguous spec, underivable threshold).

### Quality Guidelines

- No privileged operations anywhere in the bundle
- network_mode = "public" by default; "no-network" only when public internet would let the agent skip the work
- Byte-identical verifier logic for oracle and agent
- No wall-clock latency/throughput assertions
- Deterministic thresholds fixed before model trials
- Persisted state reloaded or torn down before verification — never checked only from memory or logs
- Every non-standard environment variable test.sh reads has a working default
- Verifier-executed agent code runs unprivileged, bounded, env-sanitized, no write access to /logs/verifier

### FAQ (selected)

- reward.txt not found: blocking entrypoint (e.g. `exec nginx -g 'daemon off;'`); `set -euo pipefail` exiting before the reward write; missing `mkdir -p /logs/verifier`.
- Docker network errors after many runs: `docker network prune`.
- Policy refusal in a validation run: provider refusal, not a correctness verdict.
- Review time: assessments ~24 h; task reviews 1–7 business days. New guidelines apply to new submissions only.
- Pay: Friday-to-Thursday cycle, paid the following Friday, only once Accepted.

### Glossary

Canary string (banned everywhere); CTRF (per-test result report); difficulty_explanation (plain prose); Negative Control (NC-01–14); NOP (must fail every test, every run); Oracle (must pass every test, every run); QC Rubric (task-agnostic bar); Reward hacking (editing tests, writing the reward file, reading solution/); rubric.txt (task-specific conduct criteria); Trajectory; Trial; VALID_FAIL (a failure for a genuine, defensible reason); Verifier (deterministic checker in tests/, separate container).

---

## QC Rubric (1–5 per criterion: 1–2 Major, blocks delivery · 3–4 Minor · 5 clean)

Record score + exact location/quote per criterion, re-derived from disk. Edition note: no difficulty field/tier; allow_internet → network_mode; rubric.txt and tests/Dockerfile required; outer wrapper with oracle-nop-evidence/ (Oracle ×3 + NOP ×2), trajectories/ (5 runs + SUMMARY.txt), rubric.txt; 28800 timeouts deliberate.

### instruction.md (21)

Spec Completeness · Task Framing Accuracy · Clarity / Concision Budget · No Manufactured Difficulty · No Diagnosis / Decoy Leakage · network_mode Claim Consistency · No Internal-Tool Trace / PII · No Canary Strings · No Hints / Stepwise / Detection Guidance · Absolute Paths Only · Task Name Not in Body · No LLM-Generated Prose · Env Docs Define WHAT Never HOW · Multi-Step / Agentic Depth (≥5 commands + real reasoning) · Formula/Digest Precision (diffed byte-for-byte against the compute function) · Enum/Multi-Value Rule Documentation (condition for every value) · Exact Format vs Qualitative · Decoy/Stale Doc Hygiene · Cross-File Numeric Consistency (instruction/tests/rubric) · Degenerate-Input Coverage (empty field, zero-width interval — highest-yield gap class) · Mandatory Flags Disguised as Optional.

### environment (12)

Naming Realism · No Defect/Decoy Reveal in Comments · No Solution Leakage · Dockerfile / Build Hygiene · Package Size & Runtime Fetch Discipline · Realistic Fixtures / No Hidden Coupling · Single Coherent Incident · No Internal-Tool Trace / PII (file and directory names too) · Build Platform Consistency · No Hidden Test/Solution Access · No Privileged Ops / Compose Hygiene · No AI-Scaffolding Filenames.

### solution (7)

Oracle Correctness (all three runs) · Genuine Derivation · No Dead Code / Answer Leakage · Minimal, Targeted Diff · No Generator/Meta Commentary · Literal Instruction Fidelity · Determinism / No Silent Failures.

### tests (25)

NOP Correctness (name every test_id's outcome per NOP run) · Independent Reference · Determinism · Rubric Coverage · No Exact-Match Overfitting · Diagnostic Failure Output · Test Independence · Threshold Calibration / No Near-Oracle Gate · No Wall-Clock Assertions · No PATH/Wrapper-Shim Vulnerability · Agent-Code Execution Isolation · Accept-Path Fixture Compliance · Identical Oracle/Agent Test Logic · **Per-Test Manifest & TBENCH_TEST_ID** (entries map 1:1 to CTRF names; runs everything when unset, exact selection when set, rejects unknown ids) · Negative-Control Coverage (NC-01–14) · Binary Reward, Always Written (reward.txt initialized to 0, always ends 0 or 1, zero runtime installs) · Ratio/Percentage Assertion Validity · Hand-Rolled Parser Verification · Resource-Limit Test Platform Guarding · Collection Equality Scope Consistency · Rejection-Test Positive Control · Precedence-Test Adverse Precondition · No Iteration-Count-Bounded Race · Persisted-State Verification · tests/Dockerfile Build Hygiene.

### task.toml (12)

Required Top-Level Fields · Verifier / Separate-Mode Config · Agent Timeout Configuration · network_mode Consistency · Task Name Hygiene (no "hardened"/round numbers) · Taxonomy Exactness · No Leaked Pipeline Metadata / Edition Residue · No PII · Multi-Container Metadata · Metadata Freshness After Rerun (expert_time_estimate_hours) · Metadata Field Accuracy · Four Write-Up Fields Present.

### rubric.txt (7)

Content Presence (one line per test/failure mode) · Format Compliance (no header, no test names, never `rubrics.txt`) · Score Magnitude & Sum Compliance · Instruction Alignment · Positive/Negative Balance · Weight Reasonableness · Locally Authored, Required.

### trajectories (10)

Trial Inventory · Task-Digest Binding · Completeness / No Truncation · Full Causal Trial Classification · No Reward Hacking · No False Failures / Low-Timeout Artifacts · No Difficulty Tag / No Empirical Pass-Rate Reporting · No Trials Pooled Across Digests · No PII (every run's config/result checked individually) · No Truncated Rubric Score.

### Reward-Hacking / Corpus (6)

Corpus Uniqueness / Novelty (recorded comparison) · Public-Solution Resistance (closest public solution searched, documented) · General Cheat-Simulation Checklist · Answer Reachability in the Agent Image (incl. git history) · Partial-Fix-Pass Ablation Verification (build and run the real suite) · Reward-Hacking Threat-Class Coverage.

### Structure / Packaging (5)

Package Layout · Trajectories Evidence Completeness · No Packaging Cruft (`rubrics.txt`, contributor README.md, AI scaffolding, OS junk, .git, __pycache__, *.pyc) · No Behavioral Edit Since Freeze · Final Pre-Zip Re-Verification.
