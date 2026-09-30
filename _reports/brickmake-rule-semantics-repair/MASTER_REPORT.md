# Master Ship Checklist - brickmake-rule-semantics-repair

Bundle sha `6678f6a1f0254f2e`, generated 2026-09-30 15:29. FAIL 0, STALE 0, REVIEW 0, MANUAL 0, SIGNED 47, PASS 51

| # | Sec | Check | Mode | Status | First finding |
|---|---|---|---|---|---|
| GATE | - | Measured GPT-5.6 xhigh k=5 rate passes the pool acceptance gate | auto | **PASS** |  |
| CI | - | Pool static hygiene (encoding, placeholders, apt/layers, docstrings, naming) | auto | **PASS** |  |
| 0 | A | Human-written prompt, absolute paths in backticks, outputs named, what-not-how, sensible length | assist | **SIGNED** |  |
| 1 | A | Every stated requirement is exercised by a (non-NOP-passable) test | assist | **SIGNED** |  |
| 2 | A | Every requirement a test enforces is stated | assist | **SIGNED** |  |
| 3 | A | No implementation-step ('how') sentences | assist | **SIGNED** |  |
| 4 | A | Interface contracts named in the prompt are really graded as interfaces | manual | **SIGNED** |  |
| 5 | A | No grader / test-suite / verifier / pipeline terms | auto | **PASS** |  |
| 6 | A | Stated constants and tolerances match tests byte for byte | assist | **SIGNED** |  |
| 7 | A | Every path the prompt names exists in the built image | auto | **PASS** |  |
| 8 | A | Output schema exactness in prose matches the tests and the reference | assist | **SIGNED** |  |
| 9 | A | No self-contradiction between sentences | manual | **SIGNED** |  |
| 10 | A | Prompt does not narrate each planted defect's mechanism | assist | **SIGNED** |  |
| 11 | A | No canary or GUID-shaped string in instruction.md | auto | **PASS** |  |
| 12 | B | Every environment file read through and required | manual | **SIGNED** |  |
| 13 | B | No BUG/FIXME/planted/intent comments (grep environment/ and solution/) | auto | **PASS** |  |
| 14 | B | No comments echoing author (instruction/rubric) text | assist | **SIGNED** |  |
| 15 | B | No lore/notes/attempt-log doc indexing the planted defects | assist | **SIGNED** |  |
| 16 | B | No opaque short file/module names | auto | **PASS** |  |
| 17 | B | No names that mislabel behavior | manual | **SIGNED** |  |
| 18 | B | No dead / orphaned files | auto | **PASS** |  |
| 19 | B | No unused module that already implements the answer | manual | **SIGNED** |  |
| 20 | B | No environment file byte-identical to a tests/ or solution/ file (leaked oracle) | auto | **PASS** |  |
| 21 | B | Authoritative docs consistent with instruction.md | manual | **SIGNED** |  |
| 22 | B | Every environment doc is treated as a requirement and tested | manual | **SIGNED** |  |
| 23 | B | Vendored archives/binaries carry no host metadata | auto | **PASS** |  |
| 24 | B | Agent Dockerfile never copies solution/ or tests/ nor touches reserved paths | auto | **PASS** |  |
| 25 | B | Decoys are reachable, fair and not labelled | assist | **SIGNED** |  |
| 26 | B | FROM digest-pinned, canonical base, tmux+asciinema, lang pins / apt unpinned, size, no privilege, no --platform | auto | **PASS** |  |
| 27 | C | solve.sh delta listed file by file | assist | **SIGNED** |  |
| 28 | C | Every touched file maps to a requested fix (no no-op delta) | assist | **SIGNED** |  |
| 29 | C | No out-of-scope delta | manual | **SIGNED** |  |
| 30 | C | Reference output independently re-derived as correct | manual | **SIGNED** |  |
| 31 | C | Reference never branches on a scenario/case id | assist | **SIGNED** |  |
| 32 | C | Reference encodes no private / held-out knowledge | manual | **SIGNED** |  |
| 33 | C | Agent consensus vs reference outlier checked | manual | **SIGNED** |  |
| 34 | C | No orphaned files in solution/ | auto | **PASS** |  |
| 35 | C | Each fix ablated alone produces test failures | auto | **PASS** |  |
| 36 | C | Cold oracle build runs cleanly and portably | auto | **PASS** | cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-30T08:57:52 (baselines.json) |
| 37 | D | Separate verifier: top-level artifacts, landing dirs exist in verifier image | auto | **PASS** |  |
| 38 | D | tests/Dockerfile bakes every verifier dep pinned; nothing installed at trial time | auto | **PASS** |  |
| 39 | D | test.sh: no set -e, reward always written, ends with exit 0 | auto | **PASS** |  |
| 40 | D | Zero individual tests pass under NOP | auto | **PASS** |  |
| 41 | D | Guard-style tests are coupled to real behavior | assist | **SIGNED** |  |
| 42 | D | NOP-passable guards coupled, not deleted | manual | **SIGNED** |  |
| 43 | D | Assertions do what names/docstrings claim | assist | **SIGNED** |  |
| 44 | D | Expected values never computed by agent-editable code | assist | **SIGNED** |  |
| 45 | D | Verifier's private fixtures baked independently of agent-editable copies | assist | **SIGNED** |  |
| 46 | D | Held-out scenarios really change the graded outcome | manual | **SIGNED** |  |
| 47 | D | Exactness rules enforced literally (set equality) and met by the reference | assist | **SIGNED** |  |
| 48 | D | Test tolerances equal the stated tolerances | assist | **SIGNED** |  |
| 49 | D | No string obfuscation in tests | auto | **PASS** |  |
| 50 | D | No dead test helpers / unused imports | auto | **PASS** |  |
| 51 | D | Test names describe what they check | assist | **SIGNED** |  |
| 52 | D | Fail-closed tests carry a positive control | assist | **SIGNED** |  |
| 53 | D | Evidence test counts match current tests/ | auto | **PASS** |  |
| 54 | D | Agent-produced code runs sandboxed in the verifier (unprivileged, bounded, sanitized env, killpg, no /logs/verifier write) | assist | **SIGNED** |  |
| 56 | D | No wall-clock latency/throughput assertion; any work threshold fixed a priori | assist | **SIGNED** |  |
| 57 | D | Reward binary 0/1 on every path; no oracle/identity branching | auto | **PASS** |  |
| 58 | D | Tests check correct values, not just artifact existence | manual | **SIGNED** |  |
| 59 | D | Negative controls NC-01..06 run and each rejected by its own named test; NC-07..14 run or specifically n/a (_reports/<slug>/negative_controls.toml) | manual | **SIGNED** | NC-01, NC-14 are all rejected by test_outputs.py::test_shortest_stem_selection - confirm each control has its own named  |
| 61 | E | Top-level name/artifacts; metadata, taxonomy, tags, write-ups present and accurate | assist | **SIGNED** |  |
| 62 | E | No difficulty field, tier label, percentage or pass count anywhere in the task | auto | **PASS** |  |
| 63 | E | environment_mode = "separate"; agent and verifier timeouts 28800 | auto | **PASS** |  |
| 64 | E | network_mode = "public" (or justified "no-network"); instruction claims consistent | auto | **PASS** |  |
| 65 | E | No stale-schema residue, no local paths, is_multi_container only when multi-container | auto | **PASS** |  |
| 66 | F | Every rubric line maps to a real (explicit or implicit) instruction | assist | **SIGNED** | rubric line "Agent reproduces at least one reported symptom with a scratch makefile before editing" maps to no instructi |
| 67 | F | Rubric format 'Agent ..., +/-N', >=1 negative, positives 10-40, N in {1,2,3,5} | auto | **PASS** |  |
| 68 | F | No mutually contradictory rubric lines | manual | **SIGNED** |  |
| 69 | F | No double-counted behavior (positive not re-checked as negative) | assist | **SIGNED** |  |
| 71 | F | rubric_score arithmetic consistent with rubric.txt | auto | **PASS** |  |
| 73 | G | Evidence structure exact | auto | **PASS** |  |
| 74 | G | Oracle x3 reward 1, every test passing | auto | **PASS** |  |
| 75 | G | NOP x2 reward 0, every test explicitly 'failed' | auto | **PASS** |  |
| 76 | G | NOP failures are genuine assertion mismatches | auto | **PASS** |  |
| 77 | G | Evidence newer than every graded file | auto | **PASS** |  |
| 78 | G | Evidence not duplicated (timestamps, object ids) | auto | **PASS** |  |
| 79 | H | SUMMARY.txt exactly 2 lines, no prose | auto | **PASS** |  |
| 80 | H | rubric_score.txt is pure data + citations, graded per run | auto | **PASS** |  |
| 81 | H | SUMMARY rewards match each run's reward.txt and ctrf | auto | **PASS** |  |
| 82 | H | SUMMARY sha matches a fresh recompute | auto | **PASS** |  |
| 83 | H | Trajectories newer than every graded file | auto | **PASS** |  |
| 84 | H | Oracle / NOP runs genuinely independent | auto | **PASS** |  |
| 85 | H | Model runs not duplicated; no full-precision float agreement across runs | auto | **PASS** |  |
| 86 | H | Each failing run's cause read from its own files | assist | **SIGNED** |  |
| 87 | H | rubric_score files not copies of each other | auto | **PASS** |  |
| 88 | H | Every verdict cites that run's own evidence; MET spot-checked | assist | **SIGNED** |  |
| 89 | H | PII / stb scrub clean in every run and evidence dir (task.path / trials_dir) | auto | **PASS** |  |
| 90 | H | No canary / GUID-shaped string in trajectories or evidence | auto | **PASS** |  |
| 91 | H | result.json model names left raw | auto | **PASS** |  |
| 92 | H | agent/ file sets identical; verifier/ files present, reward matches ctrf | auto | **PASS** |  |
| 93 | H | reasoning_effort xhigh on every run | auto | **PASS** |  |
| 94 | H | No exception_info; no run cut off while still progressing | assist | **SIGNED** |  |
| 95 | H | Reward-hacking scan on every trajectory; genuine completion | assist | **SIGNED** | [95] run-02: trajectory mentions grading paths ['/tests/'] — read and confirm no reads/writes (no agent command touched  |
| 96 | H | Evidence regenerated atomically after the last rerun | auto | **PASS** |  |
| 97 | I | Difficulty comes from genuine reasoning; source classified in plain language | manual | **SIGNED** |  |
| 98 | I | Delivery structure exact, no junk, no AI scaffolding | auto | **PASS** |  |
| 99 | I | Final stb / personal-path / canary scrub across the whole bundle | auto | **PASS** |  |

## Findings and sign-offs

### 0 - Human-written prompt, absolute paths in backticks, outputs named, what-not-how, sensible length [SIGNED]
- sign-off (pass): instruction.md:1-8 is a colleague-style bug report of 4 short paragraphs/bullets; every path is backticked (`/app`, `/app/docs`, `/app/cmd/brickmake`, `/app/docs/cli.md`); the output is named at instruction.md:6 `same recipe lines, messages, exit codes and files left on disk`; it states what must hold, not how to change the engine.

### 1 - Every stated requirement is exercised by a (non-NOP-passable) test [SIGNED]
- sign-off (pass): Each requirement maps to a test that NOP fails (oracle-nop-evidence/nop-1/ctrf.json: 6/6 failed): symptom bullets instruction.md:3-4 -> test_pattern_specific_variable_order, test_shortest_stem_selection, test_directory_relative_prerequisites; `act exactly like GNU make 4.3` per /app/docs (instruction.md:6) -> all 17 scenarios in tests/cases.json incl. test_mentioned_prerequisite_ought_to_exist and test_project_builds; `Go standard library only` and `plain go build` of `/app/cmd/brickmake` (instruction.md:8) -> harness.py:84-85 in test_cli_builds_and_rebuilds; the cli.md interface -> every scenario invokes brickmake with the documented flags (harness play()).

### 2 - Every requirement a test enforces is stated [SIGNED]
- sign-off (pass): Tests only enforce: output/exit/files equal to GNU make 4.3 `-r -R` (instruction.md:6), for makefile features documented in /app/docs (every scenario in tests/cases.json uses rules.md/variables.md/updating.md constructs), build via `go build ./cmd/brickmake` with stdlib only (harness.py:76-85, instruction.md:8), and the cli.md flags (`-r -R`, goals, `V=cmd` overrides). The `brickmake:` prefix is stated at instruction.md:6 and the expectations were generated with `make:` rewritten (authoring/gen_expect.py).

### 3 - No implementation-step ('how') sentences [SIGNED]
- sign-off (pass): instruction.md:6 `Treat those docs as the spec and make brickmake match them` and instruction.md:8 `Keep it Go standard library only` are outcome constraints; no sentence names a file, function, sort or algorithm to change (no mention of implicit.go, scope.go, oughtToExist or stem ordering).

### 4 - Interface contracts named in the prompt are really graded as interfaces [SIGNED]
- sign-off (pass): The only interface named is the CLI in `/app/docs/cli.md` built from `/app/cmd/brickmake` (instruction.md:8). harness.py:76 builds exactly `go build -o ... ./cmd/brickmake` in the sandbox and every scenario runs that binary through its documented command line (`-r -R`, goals, `V=cmd` in patvars/command_line_overrides_everything); no internal Go API is graded.

### 6 - Stated constants and tolerances match tests byte for byte [SIGNED]
- sign-off (pass): The only constants in the prompt are `make -r -R`, `GNU make 4.3`, `brickmake:` prefix and the symptom flags `-O2 -fPIC -DNET` (instruction.md:3). All expectations in tests/cases.json were produced by GNU make 4.3 `make -r -R` (authoring/gen.sh, gen-output.txt) with `make:` -> `brickmake:`. The symptom is exercised by patvars/more_specific_pattern_applies_last (`CFLAGS = -O2`, `build/net/%.o: CFLAGS += -DNET`, `build/%.o: CFLAGS += -fPIC`) plus an extra `%.o: CFLAGS += -g`, so the literal string is deliberately not hard-codable (NC-03). No tolerances exist: comparison is exact (test_outputs.py:31).

### 8 - Output schema exactness in prose matches the tests and the reference [SIGNED]
- sign-off (pass): instruction.md:6 promises exact parity: `same recipe lines, messages, exit codes and files left on disk, the only difference being the brickmake: prefix`. test_outputs.py:30-34 compares stdout, stderr, exit code and `ls` listings byte for byte against GNU make output with only the prefix rewritten, and the reference passes all 17 scenarios (oracle-nop-evidence/oracle-1/ctrf.json 6/6 passed).

### 9 - No self-contradiction between sentences [SIGNED]
- sign-off (pass): Read instruction.md:1-8 end to end: the symptoms (:3-4) are examples of the parity goal (:6); `GNU make isn't installed` (:8) is consistent with `make -r -R` quoted as the colleague's reference output (:3); `only Go standard library` and `plain go build` agree; `cli.md shouldn't change` does not conflict with any other sentence.

### 10 - Prompt does not narrate each planted defect's mechanism [SIGNED]
- sign-off (pass): instruction.md:3-4 describes only observed symptoms (`brickmake gets the flags wrong`, `picks a different rule than make, or looks for a prerequisite in the wrong directory`). It never names the mechanisms (stem length excluding the directory, directory prefix on non-% prerequisites, ought-to-exist requiring a rule, pattern variables in makefile order), and the mention defect is not reported at all (`That's probably not the full list`, :6).

### 12 - Every environment file read through and required [SIGNED]
- sign-off (pass): Read all 41 files under environment/: Dockerfile + .dockerignore build the image; app/go.mod and cmd/brickmake/main.go are the build entry (instruction.md:8); internal/{cli,db,diag,engine,expand,parse,text,vars} are the tool itself (README.md:24-32 layout); docs/{cli,functions,makefiles,rules,updating,variables}.md are the spec named at instruction.md:6; README.md explains building and layout; examples/demo/{Makefile,include/demo.h,src/main.c,src/value.c} is the runnable sample from examples/demo/Makefile:4 `cd examples/demo && ../../brickmake`, which exercises `$(OUT)/%.o: src/%.c include/demo.h` (a non-% prerequisite in a pattern rule). No file is unused.

### 14 - No comments echoing author (instruction/rubric) text [SIGNED]
- sign-off (pass): `rg -n 'sock|DNET|fPIC|wrong directory|different rule' brickmake-rule-semantics-repair/brickmake-rule-semantics-repair/environment brickmake-rule-semantics-repair/brickmake-rule-semantics-repair/solution` finds no instruction or rubric phrasing in comments; implicit.go comments describe code behavior, e.g. implicit.go:72-73 `The directory of a directory-relative match is prepended to every prerequisite.`

### 15 - No lore/notes/attempt-log doc indexing the planted defects [SIGNED]
- sign-off (pass): environment/app contains only README.md and docs/*.md as prose; README.md:1-41 is build/layout/doc index, docs/*.md are GNU make semantics. `rg -n -i 'known issue|todo|bug|regression|changelog|notes' environment/app` returns nothing indexing the four defects.

### 17 - No names that mislabel behavior [SIGNED]
- sign-off (pass): Names match what the code does: implicit.go `candidates`, `prereqs`, `oughtToExist` (the rules.md:88 term), scope.go `patternSet`; the comments state the current behavior accurately (implicit.go:95-96 `oughtToExist reports whether a prerequisite exists or is a target in the makefile.`), so nothing is labelled as already correct or mislabeled.

### 19 - No unused module that already implements the answer [SIGNED]
- sign-off (pass): `rg -n fullStem environment/app` -> implicit.go:33 definition, used at implicit.go:78 (`$*` scope) and implicit.go:161 (match stem); it is live code, not a spare implementation of the fix. No other package contains an alternate implicit-rule search or pattern-variable ordering (internal/engine is the only user of db.PatternRule).

### 21 - Authoritative docs consistent with instruction.md [SIGNED]
- sign-off (pass): instruction.md:6 names /app/docs as the spec; the docs agree with GNU make 4.3 and with the tests: rules.md:69-76 (directory added only to prerequisites that contain `%`), rules.md:80-83 (stem length `directory part included, shortest first`), rules.md:87-92 (mentioned prerequisite ought to exist, `No rule to make target` if it has none), variables.md:105-113 (`applied from the shortest pattern to the longest`). README.md:5-9 repeats the `make -r -R` / `brickmake:` contract of instruction.md:6.

### 22 - Every environment doc is treated as a requirement and tested [SIGNED]
- sign-off (pass): instruction.md:6 makes every doc a requirement. The graded scenarios exercise each doc: rules.md -> stem/dirs/mention groups; variables.md -> patvars group (incl. command_line_overrides_everything); updating.md -> smoke rerun/rebuild and project/incremental_builds; makefiles.md/functions.md -> project case (`wildcard`, `patsubst`, conditionals); cli.md -> goals, `-r -R`, `V=cmd`. The five restored out-of-scope fixes keep the rest of the docs true in the shipped code, so no doc describes behavior the tests would contradict.

### 25 - Decoys are reachable, fair and not labelled [SIGNED]
- sign-off (n/a): No decoys are planted: the defects all live in internal/engine/implicit.go and scope.go (`py -3 _reports/brickmake-rule-semantics-repair/authoring/solvediff.py ...` shows only those two files) and every other package is correct working code, confirmed by oracle-nop-evidence/oracle-1/ctrf.json passing 6/6 with only those two files changed.

### 27 - solve.sh delta listed file by file [SIGNED]
- sign-off (pass): solve.sh:6 `cat > internal/engine/implicit.go` (stem sort uses `fullStem()`; directory prefix only when `strings.IndexByte(w, '%') >= 0`; oughtToExist returns true for any `e.db.Lookup(name) != nil`) and solve.sh:218 `cat > internal/engine/scope.go` (`sort.SliceStable(hits, ... len(hits[i].Pattern) < len(hits[j].Pattern))`); solve.sh:273-276 only runs gofmt and `go build`. Diff recorded by `py -3 _reports/brickmake-rule-semantics-repair/authoring/solvediff.py brickmake-rule-semantics-repair/brickmake-rule-semantics-repair`.

### 28 - Every touched file maps to a requested fix (no no-op delta) [SIGNED]
- sign-off (pass): solvediff.py output: implicit.go has 3 hunks (stem sort, `%`-only directory prefix, oughtToExist) and scope.go has 1 hunk (length sort + `sort` import); each hunk is one of the four fixes. Ablation proves each is load-bearing: _reports/brickmake-rule-semantics-repair/ablation.json u01 implicit.go -> stem/dirs/mention fail, u02 scope.go -> cli/patvars/project fail.

### 29 - No out-of-scope delta [SIGNED]
- sign-off (pass): `py -3 _reports/brickmake-rule-semantics-repair/authoring/solvediff.py ...` shows only implicit.go and scope.go changed, and only in the functions candidates, prereqs, oughtToExist and patternSet plus their doc comments; no formatting churn, no test edits, no other file touched.

### 30 - Reference output independently re-derived as correct [SIGNED]
- sign-off (pass): Expected outputs were not taken from the reference: authoring/gen.sh replays every scenario in tests/cases.json with real GNU make 4.3 `make -r -R` in the pinned golang bookworm image and authoring/gen_expect.py records stdout/stderr/exit/`ls` (log authoring/gen-output.txt). The reference then matches those independently derived values 17/17 (oracle-nop-evidence/oracle-1..3/ctrf.json). The mention case also matches rules.md:90-92 by hand: parser.c is mentioned so `%.o: %.c %.h` is skipped for the missing .h rule and GNU make prints `No rule to make target`.

### 31 - Reference never branches on a scenario/case id [SIGNED]
- sign-off (pass): `rg -n 'sock|net/|lib/a|cases|smoke|scenario' brickmake-rule-semantics-repair/brickmake-rule-semantics-repair/solution/solve.sh` matches nothing outside Go identifiers; the four changes are generic sorts and predicates (solvediff.py output) and the oracle passes scenarios it never names.

### 32 - Reference encodes no private / held-out knowledge [SIGNED]
- sign-off (pass): Every rule the reference implements is written in the shipped docs the agent can read: rules.md:74 (`%` prerequisites only), rules.md:80-81 (`directory part included`), rules.md:88-92 (ought to exist), variables.md:109-112 (shortest pattern to longest). Runs 02, 03 and 05 derived the same four fixes from those docs alone (trajectories/run-0N/rubric_score.txt lines 3-6 MET).

### 33 - Agent consensus vs reference outlier checked [SIGNED]
- sign-off (pass): Agent consensus agrees with the reference: all 5 runs made the same stem, directory and pattern-variable fixes (rubric_score.txt lines 3,4,6 MET in run-01..05); runs 02/03/05 also made the reference's oughtToExist change (`if e.db.Lookup(name) != nil`, run-02/rubric_score.txt:5). The only divergence (run-01, run-04 kept `len(f.Rules) > 0 || f.Phony`) is contradicted by GNU make 4.3 output in tests/cases.json, not by the reference.

### 36 - Cold oracle build runs cleanly and portably [PASS]
- info: cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-30T08:57:52 (baselines.json)

### 41 - Guard-style tests are coupled to real behavior [SIGNED]
- sign-off (pass): The only guard-like assertions are coupled to behavior inside a real scenario: the stdlib check (harness.py:84-85) runs inside build(), which test_cli_builds_and_rebuilds needs before replaying smoke/smoke_layered_flags_and_rerun; the rm-step check `should have been built before this step removes it` only fires when the preceding build step did not create the file. NOP fails all 6 (oracle-nop-evidence/nop-1/ctrf.json).

### 42 - NOP-passable guards coupled, not deleted [SIGNED]
- sign-off (pass): No test is NOP-passable: oracle-nop-evidence/nop-1/ctrf.json and nop-2/ctrf.json both show 6 tests `failed`, including test_cli_builds_and_rebuilds (its smoke scenario needs layered pattern variables and so fails on the shipped code, test_outputs.py:38-41).

### 43 - Assertions do what names/docstrings claim [SIGNED]
- sign-off (pass): Each test replays only its own group (test_outputs.py:22-35 `replay(group)` filters `c['group'] == group`) and each docstring states that group's rule, e.g. test_outputs.py:39-40 `compiles with the standard library only, runs a default-goal build ... and rebuilds only what was removed` = smoke case steps (build, ls, rerun, rm, rebuild) plus harness.py:84-85 stdlib assertion.

### 44 - Expected values never computed by agent-editable code [SIGNED]
- sign-off (pass): Expected values are literals in tests/cases.json (generated offline by GNU make 4.3, authoring/gen.sh) baked into the verifier image by tests/Dockerfile `COPY . /tests/`; nothing under /app computes or supplies an expectation, and the verifier only compiles /app's Go source (harness.py:76).

### 45 - Verifier's private fixtures baked independently of agent-editable copies [SIGNED]
- sign-off (pass): tests/cases.json exists only in the verifier image (tests/Dockerfile `COPY . /tests/`); the agent image has no copy (environment/ has no cases.json, check 20 PASS). Tamper test `bash _reports/brickmake-rule-semantics-repair/authoring/tamper.sh`: changing one baked expectation made the oracle fail only the owning test, so the verifier grades against its own copy.

### 46 - Held-out scenarios really change the graded outcome [SIGNED]
- sign-off (pass): Hidden scenarios change the result: NC-07 (only the two reported fixes) passes the symptom-shaped cases but fails stem and mention (negative_controls.toml NC-07, nc_out/nc07.stdout.txt:71); NC-14 (fits the docs' lib/ example only) fails stem/shortest_stem_wins_across_directories on src/b.o (nc_out/nc14.stdout.txt:36); runs 01 and 04 fixed both reported symptoms and still scored 0.

### 47 - Exactness rules enforced literally (set equality) and met by the reference [SIGNED]
- sign-off (pass): Exactness is literal: test_outputs.py:30-34 requires every result tuple (stdout, stderr, exit code, `ls` listing) equal to GNU make's and the same number of results; `ls` listings are compared as exact sorted text. The reference meets it 17/17 (oracle-nop-evidence/oracle-1/ctrf.json).

### 48 - Test tolerances equal the stated tolerances [SIGNED]
- sign-off (n/a): No tolerances are stated or used: instruction.md:6 demands identical output and test_outputs.py:31 `if g != want` is exact equality; there are no numeric comparisons.

### 51 - Test names describe what they check [SIGNED]
- sign-off (pass): Names match the replayed groups: test_cli_builds_and_rebuilds (smoke), test_shortest_stem_selection (stem), test_directory_relative_prerequisites (dirs), test_mentioned_prerequisite_ought_to_exist (mention), test_pattern_specific_variable_order (patvars), test_project_builds (project) - see tests/test_manifest.json and test_outputs.py:38-66.

### 52 - Fail-closed tests carry a positive control [SIGNED]
- sign-off (pass): The fail-closed checks carry positive controls: the stdlib assertion (harness.py:84-85) passes on the reference (oracle-1 ctrf test_cli_builds_and_rebuilds passed) and fails on the vendored module (nc_out/nc08.stdout.txt:45); the rm-step existence check passes on the reference and fails on the `-n` fake (nc_out/nc02.stdout.txt:51). Error-path scenarios (`No rule to make target`) are paired with success-path ones in the same groups.

### 54 - Agent-produced code runs sandboxed in the verifier (unprivileged, bounded, sanitized env, killpg, no /logs/verifier write) [SIGNED]
- sign-off (pass): harness.py sandboxed(): agent-built code runs as `user=USER` nobody (harness.py:44) with RLIMIT_CPU/FSIZE/NPROC (harness.py:32-34), `start_new_session=True` (harness.py:48) and `os.killpg(proc.pid, signal.SIGKILL)` on timeout and cleanup (harness.py:57, :62), env limited to RUN_ENV `PATH=/usr/bin:/bin` (harness.py:28) and GOPROXY off for builds (harness.py:23), go at a fixed path; test.sh:5 `chmod 0755 /logs/verifier` keeps it root-owned so nobody cannot write there (NC-06: nc_out/nc06.reward.txt = 0).

### 56 - No wall-clock latency/throughput assertion; any work threshold fixed a priori [SIGNED]
- sign-off (pass): `rg -n 'time\.|perf_counter|elapsed|latency' brickmake-rule-semantics-repair/brickmake-rule-semantics-repair/tests` finds only fixed timeout arguments to sandboxed() (e.g. 120/300 s in harness.py build()); no assertion depends on wall-clock duration.

### 58 - Tests check correct values, not just artifact existence [SIGNED]
- sign-off (pass): Every scenario compares values, not existence: recipe lines, messages, exit codes and exact `ls` listings (test_outputs.py:30-34). NC-04 (REPORT.md + parity_results.json) and NC-02 (`-n` prints right lines, builds nothing) both score 0 (nc_out/nc04.stdout.txt:106, nc_out/nc02.stdout.txt:244).

### 59 - Negative controls NC-01..06 run and each rejected by its own named test; NC-07..14 run or specifically n/a (_reports/<slug>/negative_controls.toml) [SIGNED]
- warn: NC-01, NC-14 are all rejected by test_outputs.py::test_shortest_stem_selection - confirm each control has its own named assertion, not one shared catch-all
- warn: NC-02, NC-12 are all rejected by test_outputs.py::test_project_builds - confirm each control has its own named assertion, not one shared catch-all
- warn: NC-05, NC-08 are all rejected by test_outputs.py::test_cli_builds_and_rebuilds - confirm each control has its own named assertion, not one shared catch-all
- warn: NC-06, NC-07 are all rejected by test_outputs.py::test_mentioned_prerequisite_ought_to_exist - confirm each control has its own named assertion, not one shared catch-all
- sign-off (pass): Shared test ids fail on distinct assertions: NC-01 vs NC-14 -> stem test, but NC-01 fails at nc_out/nc01.stdout.txt:71 on lib/a.o (all 6 tests fail) while NC-14 fails only the src/b.o half at nc_out/nc14.stdout.txt:36 (only test failing). NC-02 vs NC-12 -> project test, NC-02 on `echo ...; mkdir -p build` output (nc_out/nc02.stdout.txt:244) and the rm-step check (:51), NC-12 on empty output (nc_out/nc12.stdout.txt:247). NC-05 vs NC-08 -> cli test, NC-05 `go build ./cmd/brickmake failed` (nc_out/nc05.stdout.txt:37), NC-08 `must use the Go standard library only` (nc_out/nc08.stdout.txt:45). NC-06 vs NC-07 -> mention test; NC-06 is rejected first because its fake reward files never reach or cannot be written in the separate verifier (nc_out/nc06.reward.txt = 0), NC-07 on the real mention result (nc_out/nc07.stdout.txt:71).

### 61 - Top-level name/artifacts; metadata, taxonomy, tags, write-ups present and accurate [SIGNED]
- sign-off (pass): task.toml: top-level `name = "brickmake-rule-semantics-repair"` and `artifacts = ["/app"]` above the first table; [metadata] author_name/email anonymous, category `Software` / subcategory `Systems` (the agent must understand a build tool's rule engine), 5 tags, languages [go], expert_time_estimate_hours 3.0; difficulty/solution/verification explanations describe the 4 fixes, the 17 GNU-make-generated scenarios in six tests and the sandboxed nobody build, matching tests/ and solve.sh on disk.

### 66 - Every rubric line maps to a real (explicit or implicit) instruction [SIGNED]
- warn: rubric line "Agent reproduces at least one reported symptom with a scratch makefile before editing" maps to no instruction sentence
- warn: rubric line "Agent rebuilds brickmake and reruns its scratch makefiles after the last code change" maps to no instruction sentence (a test matches it - sign off only if it is an implicit requirement)
- warn: rubric line "Agent special-cases the file names or flags quoted in the instruction or docs examples" maps to no instruction sentence
- warn: rubric line "Agent changes the command-line interface documented in /app/docs/cli.md" maps to no instruction sentence (a test matches it - sign off only if it is an implicit requirement)
- warn: rubric line "Agent reruns an identical failing command three or more times in a row" maps to no instruction sentence
- sign-off (pass): Explicit: rubric.txt:3-6 map to instruction.md:3-4 and :6 (docs are the spec); rubric.txt:9 (shell out to GNU make) maps to instruction.md:8 `GNU make isn't installed` + `Go standard library only`; rubric.txt:11 (edit docs) maps to instruction.md:6 `Treat those docs as the spec`; rubric.txt:12 (CLI) maps to instruction.md:8 `the command-line interface in /app/docs/cli.md shouldn't change`. Implicit: rubric.txt:10 (special-casing quoted names) maps to instruction.md:6 `It'll be checked against makefiles other than the ones above`; rubric.txt:2, 7, 8 (reproduce, own makefiles, rebuild and rerun) are the verification implied by `That's probably not the full list` and `make brickmake match them` (instruction.md:6) and building with `plain go build` (instruction.md:8); rubric.txt:1 (read the docs) maps to instruction.md:6; rubric.txt:13 (rerunning a failing command 3+ times) is a generic process-quality line.

### 68 - No mutually contradictory rubric lines [SIGNED]
- sign-off (pass): Read rubric.txt:1-13: positives reward reading docs, reproducing, the four fixes, extra checks and a final rebuild; negatives penalize shelling out, special-casing, editing docs, changing the CLI and repeating a failing command. No line rewards what another penalizes (e.g. rubric.txt:7 own makefiles vs rubric.txt:10 special-casing examples concern test inputs vs production code).

### 69 - No double-counted behavior (positive not re-checked as negative) [SIGNED]
- sign-off (pass): No behavior is scored twice: fixes (rubric.txt:3-6) and the special-casing penalty (rubric.txt:10) judge different properties (correct rule vs name-keyed hack); rubric.txt:2 (reproduce before editing) and rubric.txt:8 (rerun after the last change) are different moments; rubric.txt:13 counts command repetition, which no positive line measures.

### 86 - Each failing run's cause read from its own files [SIGNED]
- sign-off (pass): run-01: trajectories/run-01/verifier/test-stdout.txt:36 `AssertionError: mention/prerequisite_mentioned_elsewhere_ought_to_exist result #1` and :49 FAILED test_mentioned_prerequisite_ought_to_exist; its agent/trajectory.json step 7 viewed oughtToExist and never edited it (run-01/rubric_score.txt:5). run-04: run-04/verifier/test-stdout.txt:36 same assertion, :49 FAILED; no edit touched oughtToExist (run-04/rubric_score.txt:5). Both read rules.md (run-01 step 2, run-04 steps 3-4), so the cause is a genuine capability failure, not a spec gap.

### 88 - Every verdict cites that run's own evidence; MET spot-checked [SIGNED]
- sign-off (pass): Every rubric_score.txt line cites that run's own agent/trajectory.json step and/or verifier/test-stdout.txt line (e.g. run-04/rubric_score.txt:3 `step 5` + `verifier/test-stdout.txt:45`). Spot-checked MET lines: run-02/rubric_score.txt:5 `if e.db.Lookup(name) != nil` against run-02 step 5, and run-02/verifier/test-stdout.txt:14 `PASSED ../tests/test_outputs.py::test_mentioned_prerequisite_ought_to_exist` - both present.

### 94 - No exception_info; no run cut off while still progressing [SIGNED]
- sign-off (pass): PowerShell `ConvertFrom-Json` over trajectories/run-0*/result.json: run-01..05 all `exc=False` (exception_info null), rewards 0,1,1,0,1 matching SUMMARY.txt line 2 `[0, 1, 1, 0, 1]`. Each agent ended by declaring the task complete (task_complete in the final trajectory step), well under the 28800 s agent timeout, so no run was cut off.

### 95 - Reward-hacking scan on every trajectory; genuine completion [SIGNED]
- info: [95] run-02: trajectory mentions grading paths ['/tests/'] — read and confirm no reads/writes (no agent command touched them - mention is in output/prose only)
- sign-off (pass): Scanned all 5 agent/trajectory.json files for /tests, /logs/verifier, reward.txt, ctrf: the only hit is run-02's plan text `run gofmt/tests/build` (a list of steps, no command touching /tests). No run wrote reward files or special-cased scenario names; passing runs 02/03/05 made the four generic engine fixes (rubric_score.txt:3-6 MET, :10 NOT MET special-casing).

### 97 - Difficulty comes from genuine reasoning; source classified in plain language [SIGNED]
- sign-off (pass): task.toml difficulty_explanation explains in plain language that the reported symptoms cover only two of the four rules, and the other two (stem length including the directory, a mentioned-but-ruleless prerequisite still counting in the first pass) must be read from rules.md:80-92 and matched to GNU make 4.3 without GNU make available. The runs bear this out: runs 01 and 04 read rules.md and still missed the ought-to-exist rule (run-01/verifier/test-stdout.txt:36), which is reasoning about semantics, not setup friction or hidden information.

## Appendix - Instruction paths (check 7)

- `/app` (instruction.md:1) -> environment/app
- `/app/docs` (instruction.md:6) -> environment/app/docs
- `/app/cmd/brickmake` (instruction.md:8) -> environment/app/cmd/brickmake
- `/app/docs/cli.md` (instruction.md:8) -> environment/app/docs/cli.md

## Appendix - Stated constants (checks 6, 48)

- instruction.md:6 `4.3` -> present in tests/

## Appendix - Solution delta (checks 27-29, 35)

- `/app/internal/engine/implicit.go` via heredoc at solve.sh:6-216 -> environment/app/internal/engine/implicit.go: +11 / -6 lines
- `/app/internal/engine/scope.go` via heredoc at solve.sh:218-271 -> environment/app/internal/engine/scope.go: +6 / -1 lines

## Appendix - Tests (checks 43, 51)

- tests/test_outputs.py:38 test_cli_builds_and_rebuilds - /app/cmd/brickmake compiles with the standard library only, runs a default-goal
- tests/test_outputs.py:44 test_shortest_stem_selection - Among matching pattern rules the one with the shortest stem wins, where the
- tests/test_outputs.py:50 test_directory_relative_prerequisites - For a slash-less target pattern matched against a name with a directory, the
- tests/test_outputs.py:56 test_mentioned_prerequisite_ought_to_exist - A prerequisite that is mentioned anywhere in the makefile counts as one that
- tests/test_outputs.py:62 test_pattern_specific_variable_order - Pattern-specific variables from all matching patterns apply from the shortest
- tests/test_outputs.py:68 test_project_builds - Multi-step incremental builds of small projects produce the same commands,

## Appendix - Negative controls (check 59)

- NC-01 run -> test_outputs.py::test_shortest_stem_selection
- NC-02 run -> test_outputs.py::test_project_builds
- NC-03 run -> test_outputs.py::test_pattern_specific_variable_order
- NC-04 run -> test_outputs.py::test_directory_relative_prerequisites
- NC-05 run -> test_outputs.py::test_cli_builds_and_rebuilds
- NC-06 run -> test_outputs.py::test_mentioned_prerequisite_ought_to_exist
- NC-07 run -> test_outputs.py::test_mentioned_prerequisite_ought_to_exist
- NC-08 run -> test_outputs.py::test_cli_builds_and_rebuilds
- NC-09 n/a -> brickmake's output is its stdout/stderr/exit status plus the files its recipes create. There is no separate co
- NC-10 n/a -> Inputs are makefile scenarios, not data sets. There is no size, first-N or sorted-record dimension to shortcut
- NC-11 n/a -> The only thing the verifier takes from the agent side is the Go source under /app that it compiles. Scenarios 
- NC-12 run -> test_outputs.py::test_project_builds
- NC-13 n/a -> There is no scale axis: every scenario is a handful of files in a fresh scratch directory, and brickmake is re
- NC-14 run -> test_outputs.py::test_shortest_stem_selection

## Appendix - Rubric map (checks 66, 69)

- `Agent reads the pattern rule and pattern-specific variable sections of /app/docs (rules.md` (+2) -> test `test_pattern_specific_variable_order` (3 shared words); instruction.md:1 (4)
- `Agent reproduces at least one reported symptom with a scratch makefile before editing` (+2) -> test `test_shortest_stem_selection` (1 shared words); instruction.md:1 (1)
- `Agent fixes pattern-rule selection so the stem length includes the directory part of a dir` (+5) -> test `test_shortest_stem_selection` (7 shared words); instruction.md:4 (2)
- `Agent limits the directory prefix of a directory-relative match to prerequisites that cont` (+3) -> test `test_directory_relative_prerequisites` (5 shared words); instruction.md:4 (2)
- `Agent treats a prerequisite that is mentioned anywhere in the makefile as one that ought t` (+5) -> test `test_mentioned_prerequisite_ought_to_exist` (10 shared words); instruction.md:4 (3)
- `Agent applies matching pattern-specific variables from the shortest pattern to the longest` (+3) -> test `test_pattern_specific_variable_order` (9 shared words); instruction.md:1 (3)
- `Agent writes its own makefiles for cases beyond the two reported symptoms to check the imp` (+3) -> test `test_mentioned_prerequisite_ought_to_exist` (3 shared words); instruction.md:1 (2)
- `Agent rebuilds brickmake and reruns its scratch makefiles after the last code change` (+2) -> test `test_cli_builds_and_rebuilds` (2 shared words); instruction.md:1 (1)
- `Agent makes brickmake shell out to or embed GNU make instead of fixing its own logic` (-5) -> test `test_cli_builds_and_rebuilds` (1 shared words); instruction.md:1 (2)
- `Agent special-cases the file names or flags quoted in the instruction or docs examples` (-5) -> test `test_pattern_specific_variable_order` (1 shared words); instruction.md:1 (1)
- `Agent edits /app/docs to match the existing behavior instead of fixing the code` (-3) -> test `test_shortest_stem_selection` (1 shared words); instruction.md:6 (2)
- `Agent changes the command-line interface documented in /app/docs/cli.md` (-3) -> test `test_pattern_specific_variable_order` (2 shared words); instruction.md:6 (1)
- `Agent reruns an identical failing command three or more times in a row` (-1) -> test `test_pattern_specific_variable_order` (1 shared words); instruction.md:1 (0)

## Appendix - Runs (checks 86, 95)

- run-01: 20 steps, grading-path commands: 0, failed tests: test_mentioned_prerequisite_ought_to_exist
- run-02: 17 steps, grading-path commands: 0, failed tests: none
- run-03: 8 steps, grading-path commands: 0, failed tests: none
- run-04: 12 steps, grading-path commands: 0, failed tests: test_mentioned_prerequisite_ought_to_exist
- run-05: 14 steps, grading-path commands: 0, failed tests: none

## Appendix - Leak scan (check 20)

- no file under tests/ or solution/ is byte-identical to an environment/ file (files >= 64 bytes)

## Appendix - Float duplication (check 85)

- 0 full-precision value(s) shared across runs (excluding values present in environment/tests/solution)

## Appendix - Ablation (check 35)

- `/app/internal/engine/implicit.go` removed -> reward 0.0, failing: test_shortest_stem_selection, test_directory_relative_prerequisites, test_mentioned_prerequisite_ought_to_exist
- `/app/internal/engine/scope.go` removed -> reward 0.0, failing: test_cli_builds_and_rebuilds, test_pattern_specific_variable_order, test_project_builds
