# Master Ship Checklist - tickwheel-oncalendar-repair

Bundle sha `d1f54e8a8f1c3480`, generated 2026-09-27 00:38. FAIL 0, STALE 0, REVIEW 0, MANUAL 0, SIGNED 42, PASS 45

| # | Sec | Check | Mode | Status | First finding |
|---|---|---|---|---|---|
| CI | - | CI / pool static gates (pinned deps, base image, test.sh, docstrings, ruff, diversity) | auto | **SIGNED** | [diversity] 0/5 solved = CHALLENGE — needs a written justification that the failure is real capability |
| 0 | A | Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens | assist | **SIGNED** |  |
| 1 | A | Every stated requirement is exercised by a test | assist | **SIGNED** |  |
| 2 | A | Every requirement a test enforces is stated | assist | **SIGNED** |  |
| 3 | A | No implementation-step ('how') sentences | assist | **SIGNED** |  |
| 4 | A | Interface contracts named in the prompt are really graded | manual | **SIGNED** |  |
| 5 | A | No grader / test-suite / pipeline terms | auto | **PASS** |  |
| 6 | A | Stated constants match tests byte for byte | assist | **SIGNED** | instruction.md:8 states `252` but no equal literal exists in tests/ - confirm it is enforced or purely illustrative |
| 7 | A | Every path the prompt names exists in the built image | auto | **PASS** |  |
| 8 | A | Output schema exactness in prose matches the tests | assist | **SIGNED** |  |
| 9 | A | No self-contradiction between sentences | manual | **SIGNED** |  |
| 10 | A | Prompt does not narrate each planted defect's mechanism | assist | **SIGNED** |  |
| 11 | B | Every environment file is required | manual | **SIGNED** |  |
| 12 | B | No BUG/FIXME/planted/intent comments (grep) | auto | **PASS** |  |
| 13 | B | No comments echoing instruction or rubric text | assist | **SIGNED** |  |
| 14 | B | No lore/notes doc indexing the planted defects | assist | **SIGNED** |  |
| 15 | B | No opaque short file/module names | auto | **PASS** |  |
| 16 | B | No names that mislabel behavior | manual | **SIGNED** |  |
| 17 | B | No dead / orphaned files | auto | **PASS** |  |
| 18 | B | No unused module that already implements the answer | manual | **SIGNED** |  |
| 19 | B | Authoritative docs consistent with instruction.md | manual | **SIGNED** |  |
| 20 | B | Non-authoritative docs hold no hidden graded rule | manual | **SIGNED** |  |
| 21 | B | Vendored archives/binaries carry no host metadata | auto | **PASS** |  |
| 22 | B | Dockerfile never copies solution/ or tests/ | auto | **PASS** |  |
| 23 | B | Decoys are reachable, fair and not labelled | assist | **SIGNED** |  |
| 24 | C | solve.sh delta listed file by file | assist | **SIGNED** |  |
| 25 | C | Every touched file maps to a requested fix (no no-op delta) | assist | **SIGNED** |  |
| 26 | C | No out-of-scope delta | manual | **SIGNED** |  |
| 27 | C | Reference output independently re-derived | manual | **SIGNED** |  |
| 28 | C | Agent consensus vs reference outlier checked | manual | **SIGNED** |  |
| 29 | C | No orphaned files in solution/ | auto | **PASS** |  |
| 30 | C | Each fix ablated alone produces test failures | auto | **PASS** |  |
| 31 | C | Cold linux/amd64 oracle build runs cleanly | auto | **PASS** | cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-26T23:41:13 (baselines.json) |
| 32 | D | Zero individual tests pass under NOP | auto | **PASS** |  |
| 33 | D | Guard-style tests are coupled to real behavior | assist | **SIGNED** |  |
| 34 | D | NOP-passable guards coupled, not deleted | manual | **SIGNED** |  |
| 35 | D | Assertions do what names/docstrings claim | assist | **SIGNED** |  |
| 36 | D | Expected values never computed by agent-editable code | assist | **SIGNED** |  |
| 37 | D | Fixtures feeding expected values are not agent-editable | assist | **SIGNED** |  |
| 38 | D | Held-out scenarios really change the graded outcome | manual | **SIGNED** |  |
| 39 | D | Exactness rules enforced literally (set equality) | assist | **SIGNED** |  |
| 40 | D | Test tolerances equal the stated tolerances | assist | **SIGNED** |  |
| 41 | D | No string obfuscation in tests | auto | **PASS** |  |
| 42 | D | No dead test helpers | auto | **PASS** |  |
| 43 | D | Test names describe what they check | assist | **SIGNED** |  |
| 44 | D | Fail-closed tests carry a positive control | assist | **SIGNED** |  |
| 45 | D | Evidence test counts match current tests/ | auto | **PASS** |  |
| 46 | E | schema_version = "1.1" is the first line | auto | **PASS** |  |
| 47 | E | description/keywords/authors/category/tags accurate | assist | **SIGNED** |  |
| 48 | E | All timeouts are 7200 | auto | **PASS** |  |
| 49 | E | No reference_pattern / pipeline metadata | auto | **PASS** |  |
| 50 | E | allow_internet = true and no offline instruction | auto | **PASS** |  |
| 51 | F | Every rubric line maps to a test or instruction | assist | **SIGNED** | rubric line "Agent reads /app/docs (elapse.md, timezones.md, normalization.md, syntax.md) before changing the eng" maps  |
| 52 | F | Rubric format 'Agent ..., +/-N', no headers/blank lines | auto | **PASS** |  |
| 53 | F | No mutually contradictory rubric lines | manual | **SIGNED** |  |
| 54 | F | No double-counted behavior | assist | **SIGNED** |  |
| 55 | F | rubric_score arithmetic consistent with rubric.txt | auto | **PASS** |  |
| 56 | F | Rubric cites only mechanisms that exist | auto | **PASS** |  |
| 57 | H | Evidence structure exact | auto | **PASS** |  |
| 58 | H | Oracle x3 full credit, every test passing | auto | **PASS** |  |
| 59 | H | NOP x2 zero credit, every test 'failed' | auto | **PASS** |  |
| 60 | H | NOP failures are genuine assertion mismatches | auto | **PASS** |  |
| 61 | H | Evidence newer than every graded file | auto | **PASS** |  |
| 62 | H | Evidence not duplicated | auto | **PASS** |  |
| 63 | G | SUMMARY.txt exactly 2 lines | auto | **PASS** |  |
| 64 | G | rubric_score.txt is pure data + citations | auto | **PASS** |  |
| 65 | G | SUMMARY rewards match each run's reward.txt and ctrf | auto | **PASS** |  |
| 66 | G | SUMMARY sha matches a fresh recompute | auto | **PASS** |  |
| 67 | G | Trajectories newer than every graded file | auto | **PASS** |  |
| 68 | G | Oracle runs independent | auto | **PASS** |  |
| 69 | G | NOP runs independent | auto | **PASS** |  |
| 70 | G | Each failing run's cause read from its own files | assist | **SIGNED** |  |
| 71 | G | rubric_score files not copies of each other | auto | **PASS** |  |
| 72 | G | NOT MET / negative verdicts cite that run's own evidence | assist | **SIGNED** |  |
| 73 | G | MET verdicts spot-checked against the trajectory | assist | **SIGNED** |  |
| 74 | G | PII scrub clean across trajectory files | auto | **PASS** |  |
| 75 | G | config.json paths scrubbed to /terminal-bench2.1/<slug> | auto | **PASS** |  |
| 76 | G | result.json model names left raw | auto | **PASS** |  |
| 77 | G | agent/ file sets identical across runs | auto | **PASS** |  |
| 78 | G | verifier/ files present, reward matches ctrf | auto | **PASS** |  |
| 79 | G | reasoning_effort xhigh on every run | auto | **PASS** |  |
| 80 | G | No exception_info in any result.json | auto | **PASS** |  |
| 81 | G | Reward-hacking scan on every trajectory | assist | **SIGNED** | [81] run-02: trajectory mentions grading paths ['/tests/'] — read and confirm no reads/writes (no agent command touched  |
| 82 | G | Evidence regenerated atomically after the last k=5 | auto | **PASS** |  |
| 83 | I | Difficulty comes from genuine reasoning, source classified | manual | **SIGNED** |  |
| 84 | I | Delivery structure exact, no junk | auto | **PASS** |  |
| 85 | I | Final stb / personal-path scrub across the whole bundle | auto | **PASS** |  |

## Findings and sign-offs

### CI - CI / pool static gates (pinned deps, base image, test.sh, docstrings, ruff, diversity) [SIGNED]
- warn: [diversity] 0/5 solved = CHALLENGE — needs a written justification that the failure is real capability
- sign-off (pass): 0/5 CHALLENGE justified in _reports/tickwheel-oncalendar-repair/challenge_justification.md: every failing behaviour is stated with an example in the docs named as the spec (normalization.md:13 `0..10/3 becomes 00..09/3`, syntax.md:92 `*/5 is invalid`, elapse.md:74 `~1..3 in a 31-day month covers days 29 … 31`, syntax.md:64 year rule); run-01 and run-05 printed elapse.md in full (`cat docs/elapse.md`) and still left matching.rs untouched, so their six `~` cases fail with output byte-identical to the shipped program (compared with oracle-nop-evidence/nop-1/test-stdout.txt); runs 02-04 only grepped the docs for DST terms and stopped at the named symptoms. 15 trials over three shas of the same code all measured 0/5 with 2-6/10 tests, so the result is stable. task.toml difficulty is `hard` (the closest accepted label); the remaining tb21_check warning is this CHALLENGE note only.

### 0 - Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens [SIGNED]
- sign-off (pass): instruction.md is 10 lines (about 200 words, far under 1500 tokens), written as a teammate's bug report (`We check our systemd timer schedules in CI with tickwheel`); every absolute path is in backticks: `/app` (instruction.md:1), `/app/docs/cli.md` and `/app/docs` (instruction.md:8, 10); the graded output is named at instruction.md:8: `same rows, same timestamps, same errors and exit codes`.

### 1 - Every stated requirement is exercised by a test [SIGNED]
- sign-off (pass): Each stated item maps to tests/cases.json: Dublin repeat -> offset_folding `*:30 Europe/Dublin`; Lord Howe/Havana -> dst_gap `*-*-* 02:30 Australia/Lord_Howe`, `*-*-* 02:30 America/Havana`; `Fri..Mon 18:00` -> rejected_expressions; `Sat,Sun 10:00` -> normalized_forms; exact systemd output -> tests/test_outputs.py:86 compares (rc, stdout, stderr); std-only/no unsafe/FFI/other programs -> tests/test_outputs.py:28-56 source policy; CLI from cli.md -> tests/test_outputs.py:74 invokes `calendar --base-time=... --iterations=N`; `cargo build --release` keeps working -> tests/test_outputs.py:66.

### 2 - Every requirement a test enforces is stated [SIGNED]
- sign-off (pass): Everything the tests enforce is stated: output equality (instruction.md:8 `print exactly what systemd-analyze calendar ... prints`), stderr limited to `Failed...` lines because cli.md lists `No hint lines after parse errors` as an intended difference, Cargo.lock with only tickwheel (instruction.md:10 `no crates`), `unsafe`/`extern`/`#[link]` (instruction.md:10 `no unsafe or FFI`), `process::Command`/`Command::new` (instruction.md:10 `no running other programs`), build with `--offline --locked` works for a crate without dependencies (instruction.md:10). The policy strips comments first (tests/test_outputs.py:37) so prose mentions are not penalised.

### 3 - No implementation-step ('how') sentences [SIGNED]
- sign-off (pass): instruction.md gives symptoms (instruction.md:3-6), the target behaviour (instruction.md:8) and constraints (instruction.md:10); there is no sentence telling the agent which file, function or algorithm to change.

### 4 - Interface contracts named in the prompt are really graded [SIGNED]
- sign-off (pass): The only interface named is the command line of `/app/docs/cli.md` (instruction.md:10); tests/test_outputs.py:74-79 calls `tickwheel calendar --base-time=<base> UTC --iterations=N EXPR...` exactly as cli.md documents and grades stdout, `Failed` stderr lines and the exit code.

### 6 - Stated constants match tests byte for byte [SIGNED]
- warn: instruction.md:8 states `252` but no equal literal exists in tests/ - confirm it is enforced or purely illustrative
- sign-off (pass): `252` at instruction.md:8 is the systemd major version in `systemd 252 (Debian bookworm, 252.39)`; it is descriptive. The graded version `252.39` is present in tests (docstring at tests/test_outputs.py:1-2 and the generator string in tests/cases.json), and every expected output was recorded from that systemd-analyze build.

### 8 - Output schema exactness in prose matches the tests [SIGNED]
- sign-off (pass): instruction.md:8 asks for the same rows, timestamps, errors and exit codes apart from the differences listed in cli.md; tests/test_outputs.py:86 compares exit code, the full stdout and the stderr lines starting with `Failed` (tests/test_outputs.py:78), which is exactly what cli.md's `Differences from systemd-analyze` section leaves (no `From now:` rows, no hint lines).

### 9 - No self-contradiction between sentences [SIGNED]
- sign-off (pass): Read instruction.md line by line: symptoms, the `That's probably not everything` sentence, the docs-as-spec sentence and the constraints do not conflict; the 'other expressions, zones and dates' sentence (instruction.md:8) is consistent with the held-out cases in tests/cases.json.

### 10 - Prompt does not narrate each planted defect's mechanism [SIGNED]
- sign-off (pass): instruction.md:3-6 describe observable symptoms only (`prints the same elapse time on every row`, `gets accepted and scheduled, systemd refuses it`); none names a mechanism such as the mktime probe preference, the stuck check, the bounds reset or the range trimming.

### 11 - Every environment file is required [SIGNED]
- sign-off (pass): Read every file under environment/: Dockerfile builds the image; .dockerignore keeps target/ out; Cargo.toml/Cargo.lock are needed for `cargo build --locked`; README.md is the project readme with the layout table; the five docs are the spec named in instruction.md:8; all 18 .rs files are compiled modules reachable from src/main.rs (mod declarations in main.rs, civil/mod.rs, engine/mod.rs, spec/mod.rs, zone/mod.rs).

### 13 - No comments echoing instruction or rubric text [SIGNED]
- sign-off (pass): Read every comment in environment/app/src. The three defect-site comments that echoed author text were removed before the final bundle (parse.rs weekday wrap and `*/N` comments; normalize.rs now says `/// Expands two-digit years to four digits.`), and next.rs:124 now reads `// Folding changed the time; match again from there.` instead of paraphrasing elapse.md step 5. No remaining comment restates instruction.md or a docs sentence.

### 14 - No lore/notes doc indexing the planted defects [SIGNED]
- sign-off (pass): environment/ has no lore/notes/history file; README.md only has a per-directory layout table (`src/spec/` expression parser, normalization...), not a per-defect list; docs/*.md describe the intended behaviour, not defects.

### 16 - No names that mislabel behavior [SIGNED]
- sign-off (pass): Function names match behaviour: `fix_year` expands years, `find_matching_component` returns the earliest matching value, `tm_within_bounds` folds and reports movement, `mktime` converts wall time, `format_weekdays` prints weekday runs; no name claims a different job.

### 18 - No unused module that already implements the answer [SIGNED]
- sign-off (pass): All 18 .rs files under environment/app/src are declared and reachable: main.rs:1-8 declares `mod civil; mod cli; mod engine; mod errno; mod spec; mod table; mod timestamp; mod zone;`, civil/mod.rs:7 `pub mod mktime;`, zone/mod.rs:3-4 `pub mod rule; pub mod tzif;`, engine/mod.rs:3-5 `mod bounds; mod matching; mod next;`, spec/mod.rs:3-5 `mod format; mod normalize; mod parse;`. grep for a second parser/engine/mktime implementation (`fn parse_calendar`, `fn mktime`, `fn next_elapse`) finds one definition each; no dead module contains the fixed logic.

### 19 - Authoritative docs consistent with instruction.md [SIGNED]
- sign-off (pass): instruction.md:8 says the docs are the spec and targets systemd 252.39 under `TZ=UTC`; cli.md:7-9 says the same (`drop-in for systemd-analyze calendar as shipped with systemd 252 (Debian bookworm, 252.39), run with TZ=UTC`); the CLI constraint at instruction.md:10 points to cli.md. No ordering, format or edge-case rule differs between them.

### 20 - Non-authoritative docs hold no hidden graded rule [SIGNED]
- sign-off (pass): The only non-authoritative doc is environment/app/README.md; its one example (`Mon..Fri 09:30 Europe/Berlin` from 2026-03-28 12:00 UTC) matches real systemd-analyze 252.39 output and it states no rule beyond the docs.

### 23 - Decoys are reachable, fair and not labelled [SIGNED]
- sign-off (n/a): No decoys were planted: every file in environment/ is either the working program (`environment/app/src/**/*.rs`, `Cargo.toml`, `Cargo.lock`), its spec (`environment/app/docs/*.md`) or the Dockerfile; MASTER_REPORT appendix `Path map` lists no file that is unreferenced by the build or the instruction, so there is nothing to label or make reachable.

### 24 - solve.sh delta listed file by file [SIGNED]
- sign-off (pass): solve.sh rewrites 9 files by heredoc (MASTER_REPORT appendix `Solution delta`): mktime.rs +1/-1 (gap preference), bounds.rs (next-smaller-field reset + doc paragraph), matching.rs +3 (end-of-month swap), engine/mod.rs (hint carried in `&mut self.offset` + doc sentence), next.rs (stuck check + keep_isdst), format.rs +2/-2 (two-day weekday run), normalize.rs (range-end trim + 19xx years), parse.rs (reject backwards weekday ranges and `*/N`), rule.rs +1/-1 (`mday0 + 7 >= dim`).

### 25 - Every touched file maps to a requested fix (no no-op delta) [SIGNED]
- sign-off (pass): Each of the 9 touched files carries one or two defects and ablating it alone fails its tests (_reports/tickwheel-oncalendar-repair/ablation.json, e.g. `u09-rule-rs` -> `test_far_future_rules`, `u04-mod-rs` -> `test_dst_overlap`); the fixed behaviours are all required by the docs named in instruction.md:8.

### 26 - No out-of-scope delta [SIGNED]
- sign-off (pass): The solution delta only restores behaviour the docs specify plus two doc comments; the per-file delta (MASTER_REPORT appendix `Solution delta`) shows no change to the CLI, output format or any behaviour the docs do not describe.

### 27 - Reference output independently re-derived [SIGNED]
- sign-off (pass): Expected outputs in tests/cases.json were not produced by solution code: they were recorded from the real `systemd-analyze calendar` of systemd 252.39-1~deb12u2 (Debian bookworm) with tzdata 2025a under TZ=UTC. The oracle tree was then checked against the same systemd build on tens of thousands of generated expressions (mixed and DST-targeted differential fuzz) with 0 mismatches.

### 28 - Agent consensus vs reference outlier checked [SIGNED]
- sign-off (pass): Where the five runs agree against the reference (the `~` ranges, trimmed ranges, `*/N`), their outputs are the unmodified buggy program's output (compared with oracle-nop-evidence/nop-1/test-stdout.txt), and the reference is real systemd output, which the docs describe (`~1..3 in a 31-day month covers days 29 … 31`, `*/5 is invalid`). The reference is not the outlier.

### 30 - Each fix ablated alone produces test failures [PASS]

### 31 - Cold linux/amd64 oracle build runs cleanly [PASS]
- info: cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-26T23:41:13 (baselines.json)

### 33 - Guard-style tests are coupled to real behavior [SIGNED]
- sign-off (pass): The only guard is the source policy (tests/test_outputs.py:28-56). It is coupled to real behaviour: comments are stripped (tests/test_outputs.py:37-39) and tokens matched with word boundaries, so a comment mentioning `systemd-analyze` passes (container check: `10 passed`), while a real `std::process::Command::new("true")` fails every test (`10 errors`).

### 34 - NOP-passable guards coupled, not deleted [SIGNED]
- sign-off (pass): No test passes under NOP: oracle-nop-evidence/nop-1 and nop-2 show `10 failed`, each on a case-output mismatch; the source policy passes on the shipped tree, so it is not the reason.

### 35 - Assertions do what names/docstrings claim [SIGNED]
- sign-off (pass): Each test docstring names its group (tests/test_outputs.py:95-142, e.g. `Two-digit years map to 1970-2069.`) and the body calls `_check_group` on exactly that group of tests/cases.json, comparing exit code, stdout and `Failed` stderr lines.

### 36 - Expected values never computed by agent-editable code [SIGNED]
- sign-off (pass): Expected values come only from tests/cases.json (loaded at tests/test_outputs.py:16), which is copied in at verification time; nothing in /app computes them.

### 37 - Fixtures feeding expected values are not agent-editable [SIGNED]
- sign-off (pass): tests/cases.json lives in tests/, which is not in the image (Dockerfile only `COPY app/ /app/`) and is mounted only at verification; the agent cannot edit it.

### 38 - Held-out scenarios really change the graded outcome [SIGNED]
- sign-off (pass): tests/cases.json holds 84 cases in 10 groups (`dst_gap` 7, `dst_overlap` 6, `offset_folding` 5, `field_rollover` 9, `end_of_month` 8, `normalized_forms` 15, `two_digit_years` 9, `rejected_expressions` 15, `far_future_rules` 6, `multi_expression_reports` 4); only 4 expressions appear in instruction.md. Each held-out group flips the graded outcome: _reports/tickwheel-oncalendar-repair/ablation.json shows re-introducing any single defect gives `"reward": 0.0` with that group failing, e.g. matching.rs -> `test_end_of_month`, rule.rs -> `test_far_future_rules`, bounds.rs -> `test_field_rollover`, normalize.rs -> `test_two_digit_years`. Agents that fixed only the named symptoms (trajectories run-02..04) pass 3/10 tests, confirming the held-out groups decide the result.

### 39 - Exactness rules enforced literally (set equality) [SIGNED]
- sign-off (pass): tests/test_outputs.py:86 requires `(rc, out, err) == (case["rc"], case["stdout"], case["stderr"])` exactly - full-string stdout equality and list equality of stderr lines; no subset or fuzzy matching.

### 40 - Test tolerances equal the stated tolerances [SIGNED]
- sign-off (n/a): No numeric tolerances: every comparison is exact string/integer equality (tests/test_outputs.py:86) and instruction.md states no tolerance.

### 43 - Test names describe what they check [SIGNED]
- sign-off (pass): Test names describe their group: test_dst_gap, test_dst_overlap, test_offset_folding, test_field_rollover, test_end_of_month, test_normalized_forms, test_two_digit_years, test_rejected_expressions, test_far_future_rules, test_multi_expression_reports (tests/test_outputs.py:95-142).

### 44 - Fail-closed tests carry a positive control [SIGNED]
- sign-off (pass): Every group contains cases the shipped program already gets right as positive controls (e.g. dst_gap: the NOP fails `6 of 7 cases`, normalized_forms `12 of 15`), and the oracle passes all of them (oracle-1..3 `10 passed`).

### 47 - description/keywords/authors/category/tags accurate [SIGNED]
- sign-off (pass): task.toml: description `Make a Rust clone of systemd-analyze calendar reproduce systemd 252 output ...` matches the task; keywords systemd/oncalendar/rust/timezones/dst and tags systemd-timers/calendar-events/tzif/mktime/differential-behavior describe it; category `debugging`; authors anonymous as required; languages ["rust"]; codebase_size small (28 files under environment/).

### 51 - Every rubric line maps to a test or instruction [SIGNED]
- warn: rubric line "Agent reads /app/docs (elapse.md, timezones.md, normalization.md, syntax.md) before changing the eng" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent reproduces at least one reported symptom with the tickwheel binary before editing" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent makes the gap probing settle on the instant whose local time is flagged DST when the two alter" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent rejects "*" combined with a repetition such as "*/5"" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent edits /app/docs to match the existing behavior instead of fixing the code" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent changes the command-line interface documented in /app/docs/cli.md" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent reruns an identical failing command three or more times in a row" maps to no test and no instruction sentence - confirm what grades it
- sign-off (pass): Each flagged line is graded: docs-first and reproduce-first (lines 1-2) are process criteria read from the trajectory and backed by instruction.md:8 `The docs in /app/docs are the spec` and the symptom list; the gap line maps to test_dst_gap and timezones.md:90 `towards the side flagged DST`; `*/5` maps to test_rejected_expressions (`*:*/5`, `*/2:00`, `*:*:*/10`) and syntax.md:92; editing docs contradicts instruction.md:8 (docs are the spec); CLI changes contradict instruction.md:10 `keep the command line from /app/docs/cli.md`; the repeated-command line is a trajectory hygiene criterion.

### 53 - No mutually contradictory rubric lines [SIGNED]
- sign-off (pass): Read all 19 rubric.txt lines pairwise. The 11 positives each name a distinct fix or process step (line 1 `reads /app/docs ... before changing`, line 2 `reproduces at least one reported symptom ... before editing`, line 14 `rebuilds tickwheel and compares its output against systemd-analyze or the documented examples after the fixes`). The negatives forbid things no positive asks for: line 15 `makes tickwheel call systemd-analyze, glibc through FFI, or any other program` vs line 14 which only compares output externally; line 17 `edits /app/docs` vs line 1 which reads them; line 18 `changes the command-line interface` vs no positive touching cli.rs; line 19 `reruns an identical failing command three or more times` vs line 2 which needs one reproduction. No pair can both be earned by one action.

### 54 - No double-counted behavior [SIGNED]
- sign-off (pass): No behaviour is scored twice: lines 8 and 9 share test_normalized_forms but grade different fixes (range trimming vs two-day weekday runs), and lines 11 and 12 share test_rejected_expressions but grade different fixes (backwards weekday ranges vs `*/N`); lines 2 and 14 grade reproduction before editing vs verification after the last edit.

### 70 - Each failing run's cause read from its own files [SIGNED]
- sign-off (pass): Each run's failing tests and their causes were read from its own verifier/test-stdout.txt and agent/trajectory.json: run-01 fails dst_gap (never edited mktime.rs; `FAILED ../tests/test_outputs.py::test_dst_gap`), end_of_month, normalized_forms, two_digit_years, rejected_expressions (`*:*/5` accepted), far_future_rules; run-02/03/04 fail offset_folding, field_rollover (no bounds.rs edit), end_of_month, normalized_forms, two_digit_years, rejected_expressions; run-05 fails end_of_month, normalized_forms, two_digit_years, rejected_expressions. In all five the failing `~` cases match the NOP output (`Next elapse: Sat 2026-01-31 09:00:00 UTC` for `*-*~1..3 09:00`), i.e. the code path was never changed; multi_expression_reports fails in every run because it combines a failing expression from another group.

### 72 - NOT MET / negative verdicts cite that run's own evidence [SIGNED]
- sign-off (pass): Every NOT MET and negative line in the five rubric_score.txt files cites a fragment from that run's own trajectory.json or test-stdout.txt; citecheck (each backticked fragment must exist in the run's own files and at least one per line must not occur in all five runs) reports `citation problems: 0`, e.g. run-05:7 cites its own `grep -n '^fn \|^pub fn' src/civil/mktime.rs src/engine/next.rs ...` and run-02:12 its own `grep -n -C 12 -E 'weekday|weekdays|Weekday|\.\.' src/spec/parse.rs src/spec/mod.rs`.

### 73 - MET verdicts spot-checked against the trajectory [SIGNED]
- sign-off (pass): MET verdicts were cross-checked against the verifier: for lines 3-7, 10 and 13 a MET verdict requires the mapped test to be PASSED in that run's test-stdout.txt (verdictcheck: `verdict problems: 0` across all five runs); spot-checked run-05 line 4 (`mktime(tm, &self.zone, &mut self.offset)` present in its trajectory and `PASSED ../tests/test_outputs.py::test_dst_overlap`), run-01 line 5 (stuck check edit in next.rs and test_offset_folding PASSED) and run-05 line 14 (`apt-get install -y -qq systemd` then `diff -u /tmp/s.out /tmp/t.out` against systemd-analyze after the last edit).

### 81 - Reward-hacking scan on every trajectory [SIGNED]
- info: [81] run-02: trajectory mentions grading paths ['/tests/'] — read and confirm no reads/writes (no agent command touched them - mention is in output/prose only)
- info: [81] run-03: trajectory mentions grading paths ['/tests/'] — read and confirm no reads/writes (no agent command touched them - mention is in output/prose only)
- info: [81] run-05: trajectory mentions grading paths ['/tests/'] — read and confirm no reads/writes (no agent command touched them - mention is in output/prose only)
- sign-off (pass): Scanned every command of all five trajectories for /tests, test_outputs.py, ctrf.json, reward.txt, /logs/verifier, /opt/verifier and solution/: the only hits are `find . -maxdepth 4 -type f \( -path './tests/*' ...` style searches inside /app (run-02, run-03, run-05), where no tests directory exists; no read or write of any grading file. No hand-written output artifacts: all changes are Rust source edits followed by `cargo build --release`. truncated=0 in every run_k trial line. Each run ends in a completion step with an analysis message (`Analysis: Yes. ...`), not a crashed shell. run-05 installed systemd with apt-get to compare against systemd-analyze, which the instruction and rubric line 14 allow (allow_internet = true).

### 83 - Difficulty comes from genuine reasoning, source classified [SIGNED]
- sign-off (pass): Source classified as genuine reasoning/engineering breadth: 11 defects across parser, normalization, matching engine, a glibc-style mktime port and POSIX TZ footer rules, 4 named by symptom, the rest found only by auditing behaviour against the documented spec (instruction.md:8 `The docs in /app/docs are the spec, so make tickwheel follow them`). The DST defects need reasoning about negative-DST (Europe/Dublin) and 30-minute-DST (Lord Howe) zones. No obscurity (all rules have doc examples), no decoys, no contradictions, no compliance wall (constraints are three plain sentences). Details in _reports/tickwheel-oncalendar-repair/challenge_justification.md.

## Appendix - Instruction paths (check 7)

- `/app` (instruction.md:1) -> environment/app
- `/app/docs/cli.md` (instruction.md:8) -> environment/app/docs/cli.md
- `/app/docs` (instruction.md:8) -> environment/app/docs

## Appendix - Stated constants (checks 6, 40)

- instruction.md:5 `18` -> present in tests/
- instruction.md:8 `252` -> NOT in tests/
- instruction.md:8 `252.39` -> present in tests/

## Appendix - Solution delta (checks 24-26, 30)

- `/app/src/civil/mktime.rs` via heredoc at solve.sh:6-198 -> environment/app/src/civil/mktime.rs: +1 / -1 lines
- `/app/src/engine/bounds.rs` via heredoc at solve.sh:200-280 -> environment/app/src/engine/bounds.rs: +29 / -1 lines
- `/app/src/engine/matching.rs` via heredoc at solve.sh:282-360 -> environment/app/src/engine/matching.rs: +3 / -0 lines
- `/app/src/engine/mod.rs` via heredoc at solve.sh:362-425 -> environment/app/src/engine/mod.rs: +4 / -3 lines
- `/app/src/engine/next.rs` via heredoc at solve.sh:427-623 -> environment/app/src/engine/next.rs: +15 / -1 lines
- `/app/src/spec/format.rs` via heredoc at solve.sh:625-738 -> environment/app/src/spec/format.rs: +2 / -2 lines
- `/app/src/spec/normalize.rs` via heredoc at solve.sh:740-858 -> environment/app/src/spec/normalize.rs: +13 / -3 lines
- `/app/src/spec/parse.rs` via heredoc at solve.sh:860-1351 -> environment/app/src/spec/parse.rs: +4 / -11 lines
- `/app/src/zone/rule.rs` via heredoc at solve.sh:1353-1550 -> environment/app/src/zone/rule.rs: +1 / -1 lines

## Appendix - Tests (checks 35, 43)

- tests/test_outputs.py:95 test_dst_gap - Wall times skipped by a spring-forward change (30-minute and midnight changes included).
- tests/test_outputs.py:100 test_dst_overlap - Wall times that occur twice when clocks go back resolve to the right occurrence.
- tests/test_outputs.py:105 test_offset_folding - Schedules whose candidate folds back to or before the starting point still advance.
- tests/test_outputs.py:110 test_field_rollover - Out-of-range candidates (minute 75, day 31 in a short month) roll over without skipping elapses.
- tests/test_outputs.py:115 test_end_of_month - `~` day fields, including ranges and repetitions counted from the end of the month.
- tests/test_outputs.py:120 test_normalized_forms - Normalized form printing: range ends, repetitions, weekday runs, fractions.
- tests/test_outputs.py:125 test_two_digit_years - Two-digit years map to 1970-2069.
- tests/test_outputs.py:130 test_rejected_expressions - Expressions systemd rejects produce the same error and exit status.
- tests/test_outputs.py:135 test_far_future_rules - Instants after the last stored transition use the zone's footer rule.
- tests/test_outputs.py:140 test_multi_expression_reports - Several expressions per call: separators, partial failures and exit status.

## Appendix - Rubric map (checks 51, 54)

- `Agent reads /app/docs (elapse.md, timezones.md, normalization.md, syntax.md) before changi` (+2) -> test `test_dst_gap` (1 shared words); instruction.md:3 (1)
- `Agent reproduces at least one reported symptom with the tickwheel binary before editing` (+2) -> test `test_offset_folding` (1 shared words); instruction.md:1 (1)
- `Agent makes the gap probing settle on the instant whose local time is flagged DST when the` (+3) -> test `test_offset_folding` (1 shared words); instruction.md:3 (1)
- `Agent carries the conversion hint from one wall-time conversion to the next within a singl` (+3) -> test `test_dst_gap` (1 shared words); instruction.md:3 (2)
- `Agent restores the stuck check that adds an hour and keeps the folded DST flag when a resu` (+3) -> test `test_dst_gap` (1 shared words); instruction.md:1 (2)
- `Agent makes the bounds check reset only the next smaller field of the folded time at the f` (+2) -> test `test_field_rollover` (1 shared words); instruction.md:3 (2)
- `Agent swaps the converted start and end of an end-of-month range so it runs forward` (+2) -> test `test_field_rollover` (2 shared words); instruction.md:4 (1)
- `Agent lowers a range end to the last value reached by its repetition before normalizing th` (+1) -> test `test_normalized_forms` (3 shared words); instruction.md:3 (1)
- `Agent prints a run of exactly two weekdays as "First,Second" in the normalized form` (+1) -> test `test_normalized_forms` (4 shared words); instruction.md:6 (4)
- `Agent maps two-digit years 70-99 to 1970-1999 and 00-69 to 2000-2069` (+1) -> test `test_two_digit_years` (4 shared words); instruction.md:1 (0)
- `Agent rejects weekday ranges that run backwards instead of wrapping them around the week` (+2) -> test `test_normalized_forms` (2 shared words); instruction.md:1 (1)
- `Agent rejects "*" combined with a repetition such as "*/5"` (+1) -> test `test_end_of_month` (1 shared words); instruction.md:1 (0)
- `Agent stops the Mm.w.d footer rule from moving past the last day of the month for week 5` (+2) -> test `test_far_future_rules` (3 shared words); instruction.md:3 (1)
- `Agent rebuilds tickwheel and compares its output against systemd-analyze or the documented` (+3) -> test `test_rejected_expressions` (1 shared words); instruction.md:1 (2)
- `Agent makes tickwheel call systemd-analyze, glibc through FFI, or any other program instea` (-5) -> test `test_rejected_expressions` (1 shared words); instruction.md:1 (3)
- `Agent special-cases the zones, dates or expressions quoted in the instruction or docs exam` (-5) -> test `test_rejected_expressions` (1 shared words); instruction.md:8 (3)
- `Agent edits /app/docs to match the existing behavior instead of fixing the code` (-3) -> test `test_dst_gap` (0 shared words); instruction.md:1 (1)
- `Agent changes the command-line interface documented in /app/docs/cli.md` (-3) -> test `test_dst_gap` (1 shared words); instruction.md:8 (1)
- `Agent reruns an identical failing command three or more times in a row` (-1) -> test `test_dst_gap` (1 shared words); instruction.md:8 (1)

## Appendix - Runs (checks 70, 81)

- run-01: 33 steps, grading-path commands: 0, failed tests: test_dst_gap, test_end_of_month, test_normalized_forms, test_two_digit_years, test_rejected_expressions, test_far_future_rules, test_multi_expression_reports
- run-02: 35 steps, grading-path commands: 0, failed tests: test_offset_folding, test_field_rollover, test_end_of_month, test_normalized_forms, test_two_digit_years, test_rejected_expressions, test_multi_expression_reports
- run-03: 16 steps, grading-path commands: 0, failed tests: test_dst_gap, test_field_rollover, test_end_of_month, test_normalized_forms, test_two_digit_years, test_rejected_expressions, test_multi_expression_reports
- run-04: 36 steps, grading-path commands: 0, failed tests: test_offset_folding, test_field_rollover, test_end_of_month, test_normalized_forms, test_two_digit_years, test_rejected_expressions, test_multi_expression_reports
- run-05: 46 steps, grading-path commands: 0, failed tests: test_end_of_month, test_normalized_forms, test_two_digit_years, test_rejected_expressions, test_multi_expression_reports

## Appendix - Ablation (check 30)

- `/app/src/civil/mktime.rs` removed -> reward 0.0, failing: test_dst_gap
- `/app/src/engine/bounds.rs` removed -> reward 0.0, failing: test_field_rollover, test_multi_expression_reports
- `/app/src/engine/matching.rs` removed -> reward 0.0, failing: test_end_of_month, test_multi_expression_reports
- `/app/src/engine/mod.rs` removed -> reward 0.0, failing: test_dst_overlap
- `/app/src/engine/next.rs` removed -> reward 0.0, failing: test_offset_folding, test_multi_expression_reports
- `/app/src/spec/format.rs` removed -> reward 0.0, failing: test_normalized_forms, test_multi_expression_reports
- `/app/src/spec/normalize.rs` removed -> reward 0.0, failing: test_normalized_forms, test_two_digit_years, test_multi_expression_reports
- `/app/src/spec/parse.rs` removed -> reward 0.0, failing: test_rejected_expressions, test_multi_expression_reports
- `/app/src/zone/rule.rs` removed -> reward 0.0, failing: test_far_future_rules
