# Master Ship Checklist - pinwheel-semver-range-repair

Bundle sha `d41992208d88a638`, generated 2026-09-27 10:02. FAIL 0, STALE 0, REVIEW 0, MANUAL 0, SIGNED 42, PASS 45

| # | Sec | Check | Mode | Status | First finding |
|---|---|---|---|---|---|
| CI | - | CI / pool static gates (pinned deps, base image, test.sh, docstrings, ruff, diversity) | auto | **PASS** |  |
| 0 | A | Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens | assist | **SIGNED** |  |
| 1 | A | Every stated requirement is exercised by a test | assist | **SIGNED** |  |
| 2 | A | Every requirement a test enforces is stated | assist | **SIGNED** |  |
| 3 | A | No implementation-step ('how') sentences | assist | **SIGNED** |  |
| 4 | A | Interface contracts named in the prompt are really graded | manual | **SIGNED** |  |
| 5 | A | No grader / test-suite / pipeline terms | auto | **PASS** |  |
| 6 | A | Stated constants match tests byte for byte | assist | **SIGNED** |  |
| 7 | A | Every path the prompt names exists in the built image | auto | **PASS** |  |
| 8 | A | Output schema exactness in prose matches the tests | assist | **SIGNED** |  |
| 9 | A | No self-contradiction between sentences | manual | **SIGNED** |  |
| 10 | A | Prompt does not narrate each planted defect's mechanism | assist | **SIGNED** |  |
| 11 | B | Every environment file is required | manual | **SIGNED** |  |
| 12 | B | No BUG/FIXME/planted/intent comments (grep) | auto | **PASS** |  |
| 13 | B | No comments echoing instruction or rubric text | assist | **SIGNED** | environment/app/internal/semver/version.go:152 comment repeats author text "with the same major minor patch" |
| 14 | B | No lore/notes doc indexing the planted defects | assist | **SIGNED** |  |
| 15 | B | No opaque short file/module names | auto | **PASS** |  |
| 16 | B | No names that mislabel behavior | manual | **SIGNED** |  |
| 17 | B | No dead / orphaned files | auto | **SIGNED** | [unreferenced] environment/app/registry/ansi-glyphs.json is referenced nowhere else in the bundle (ship check 17) |
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
| 31 | C | Cold linux/amd64 oracle build runs cleanly | auto | **PASS** | cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-27T09:51:55 (baselines.json) |
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
| 44 | D | Fail-closed tests carry a positive control | assist | **SIGNED** | tests/test_outputs.py:151 test_invalid_input_rejected asserts a rejection/non-zero exit with no positive control in the  |
| 45 | D | Evidence test counts match current tests/ | auto | **PASS** |  |
| 46 | E | schema_version = "1.1" is the first line | auto | **PASS** |  |
| 47 | E | description/keywords/authors/category/tags accurate | assist | **SIGNED** |  |
| 48 | E | All timeouts are 7200 | auto | **PASS** |  |
| 49 | E | No reference_pattern / pipeline metadata | auto | **PASS** |  |
| 50 | E | allow_internet = true and no offline instruction | auto | **PASS** |  |
| 51 | F | Every rubric line maps to a test or instruction | assist | **SIGNED** | rubric line "Agent reproduces a reported symptom by running pinwheel resolve on /app/examples or pinwheel compare" maps  |
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
| 81 | G | Reward-hacking scan on every trajectory | assist | **SIGNED** | [81] run-01: trajectory mentions grading paths ['/tests/'] — read and confirm no reads/writes (no agent command touched  |
| 82 | G | Evidence regenerated atomically after the last k=5 | auto | **PASS** |  |
| 83 | I | Difficulty comes from genuine reasoning, source classified | manual | **SIGNED** |  |
| 84 | I | Delivery structure exact, no junk | auto | **PASS** |  |
| 85 | I | Final stb / personal-path scrub across the whole bundle | auto | **PASS** |  |

## Findings and sign-offs

### 0 - Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens [SIGNED]
- sign-off (pass): instruction.md is 10 lines (197 words, well under 1500 tokens) written as a teammate's bug report (instruction.md:1 `it has been getting both ranges and locks wrong`). Every absolute path is in backticks: `/app`, `/app/examples` (instruction.md:1), `/app/docs/ranges.md`, `/app/docs/resolution.md`, `/app/docs/lockfile.md`, `/app/docs/cli.md` (instruction.md:8), `/app/cmd/pinwheel` (instruction.md:10). The graded outputs are named: `pin.lock` files (instruction.md:1), range/compare behaviour `exactly like npm's semver package (7.x, default options)` and the documented CLI (instruction.md:8, 10).

### 1 - Every stated requirement is exercised by a test [SIGNED]
- sign-off (pass): Each stated item is graded: quill-log/`^0.4.1` caret symptom -> test_caret_ranges (tests/test_outputs.py:110) and the fixture locks; mesh-http 1.9.0-rc.2 for `^1.4.0` -> test_prerelease_admission (:130); stale json-lattice -> test_lock_drops_packages_no_longer_required (:175, fixture `prune`); yanked exact pin -> test_lock_yanked_releases (:185); `compare 2.1.0-beta.11 2.1.0-beta.2` -> test_prerelease_precedence (:146); npm semver 7.x behaviour -> all satisfies/compare groups in tests/cases.json recorded from node-semver 7.6.3 (tests/test_outputs.py:1); resolution/lock/CLI docs -> the byte-exact lock tests and test_resolution_failures (:200); stdlib-only/no forbidden imports/no require -> _source_policy_problems (:33-43); plain `go build` of /app/cmd/pinwheel -> the session fixture (:51-55).

### 2 - Every requirement a test enforces is stated [SIGNED]
- sign-off (pass): Everything enforced is stated: semver/range results (instruction.md:8 `behave exactly like npm's semver package (7.x, default options)`), invalid-input messages and exit codes (cli.md:40 `pinwheel: invalid version "TEXT"`, named at instruction.md:8), lock bytes (lockfile.md, named at instruction.md:8), exit 3 messages and untouched lock on failure (resolution.md:59-67, cli.md:38), unseen registries/manifests (instruction.md:8 `registries, manifests and ranges that aren't in the repo`), `require` in go.mod and forbidden imports (instruction.md:10), `go build` of ./cmd/pinwheel (instruction.md:10). The policy skips _test.go files (tests/test_outputs.py:39), so agent-written tests are not penalised.

### 3 - No implementation-step ('how') sentences [SIGNED]
- sign-off (pass): instruction.md gives symptoms (lines 3-6), the reference behaviour and spec docs (line 8) and constraints (line 10); no sentence names a file, function or algorithm to change. The only directive about approach is `Treat the docs as the spec and fix the code, not the docs.` (instruction.md:8), which is an outcome rule.

### 4 - Interface contracts named in the prompt are really graded [SIGNED]
- sign-off (pass): The interfaces named are the documented CLI (instruction.md:10 `Keep the command line as documented`) and the lock format (instruction.md:8). tests/test_outputs.py:60 runs `satisfies VERSION RANGE`, `compare A B` and `resolve --registry DIR PROJECT` exactly as cli.md:4-6 documents, checks stdout `true`/`false`/`-1..1`, `resolved N packages` (:102), exit codes 0/2/3 and stderr messages (:158, :162, :213-215), and compares pin.lock byte for byte (:107).

### 6 - Stated constants match tests byte for byte [SIGNED]
- sign-off (pass): The only stated output constant is `-1` (instruction.md:6), the wrong result the shipped binary prints; tests/cases.json precedence rows expect `1` for that ordering class and compare output is checked as `f"{want}\n"` (tests/test_outputs.py:83). The versions and ranges in the symptom list (`^0.4.1`, `^1.4.0`, 1.4.2) describe the sample projects, and the error-message formats come verbatim from cli.md:40 and resolution.md:62-66, which the tests use unchanged (tests/test_outputs.py:158, :206-207).

### 8 - Output schema exactness in prose matches the tests [SIGNED]
- sign-off (pass): lockfile.md defines the exact bytes (2-space indent, key order, `<`, `>` and `&` literal at lockfile.md:9, trailing newline) and tests/test_outputs.py:107 requires `actual == expected` on the whole file; cli.md says `Prints true or false followed by a newline` and `-1, 0 or 1 followed by a newline`, and tests/test_outputs.py:70 and :83 compare `(rc, out)` to exactly that. Error checks use `err.startswith('pinwheel: invalid version "V"')` (:158) matching cli.md:40-41, and failure stderr is compared exactly (:215) to resolution.md:62-66.

### 9 - No self-contradiction between sentences [SIGNED]
- sign-off (pass): Read instruction.md sentence by sentence: the symptom list, `I doubt that's all of it.`, the npm-semver reference plus docs-as-spec sentence, the unseen-inputs sentence and the constraints paragraph are consistent; ranges.md:5-7 defers to semver 7.x `Where this page is silent`, matching instruction.md:8, and the docs never ask for anything the constraints forbid.

### 10 - Prompt does not narrate each planted defect's mechanism [SIGNED]
- sign-off (pass): instruction.md:3-6 only describe observable results (`storefront locks quill-log 0.9.2 for ^0.4.1`, `still lists json-lattice, which nothing depends on anymore`, `won't resolve because ember-uuid 1.4.2 is yanked`, `prints -1`); none names a mechanism (caret upper bound, prerelease triple gate, in-place selection update, `=`-only pin detection, lexical identifier compare). Nine of the thirteen defects (tilde, x-range, hyphen, `||` spacing, build metadata, leading zeros, override merge, lowest tie-break, HTML escaping) are not mentioned at all.

### 11 - Every environment file is required [SIGNED]
- sign-off (pass): All 46 files under environment/ are used: Dockerfile builds the image (`RUN go build -o /usr/local/bin/pinwheel ./cmd/pinwheel`), .dockerignore keeps junk out of the context, go.mod defines the module, the 22 non-test .go files are compiled into cmd/pinwheel (every package is imported from main.go -> internal/cli -> semver/semrange/registry/manifest/resolve/lockfile), the two _test.go files are the project's unit tests run by solve.sh (`go test ./...`), README.md is the project readme, the five docs are the spec named in instruction.md:8 (registry.md is linked from README.md:29 and describes the registry/manifest files), the 10 registry/*.json files are the default registry loaded by registry.go:42, and the three examples/*/pin.json are the sample projects named in instruction.md:1.

### 13 - No comments echoing instruction or rubric text [SIGNED]
- warn: environment/app/internal/semver/version.go:152 comment repeats author text "with the same major minor patch"
- sign-off (pass): version.go:152-153 is the doc comment of Floor(): `// Floor returns the lowest version with the same major.minor.patch, which is // the "-0" prerelease of that triple.` It describes what Floor returns (used for `<X.Y.Z-0` upper bounds) and is correct in both the shipped and the fixed tree; it is not at a defect site (the prerelease gate is in range.go testSet) and gives no hint about the bug. The earlier SameTriple comment that paraphrased the rubric was reworded before evidence was captured; no other comment restates instruction.md or a rubric line.

### 14 - No lore/notes doc indexing the planted defects [SIGNED]
- sign-off (pass): environment/app has no notes, changelog or history file; README.md only lists the layout (`internal/semrange - range parsing and matching`, `internal/resolve - resolution rounds and release choice`) and the docs; docs/*.md describe intended behaviour, never defects.

### 16 - No names that mislabel behavior [SIGNED]
- sign-off (pass): Names match behaviour: `caret`, `tilde`, `xrange`, `hyphen` expand the named range forms, `Compare` orders versions, `SameTriple` compares major.minor.patch, `Floor` returns the -0 prerelease, `pinned` decides exact pins, `choose` picks a release, `effective` returns the constraints after overrides, `Encode` writes the lock; no name claims a different job than the correct code performs.

### 17 - No dead / orphaned files [SIGNED]
- warn: [unreferenced] environment/app/registry/ansi-glyphs.json is referenced nowhere else in the bundle (ship check 17)
- warn: [unreferenced] environment/app/registry/ember-uuid.json is referenced nowhere else in the bundle (ship check 17)
- warn: [unreferenced] environment/app/registry/fern-config.json is referenced nowhere else in the bundle (ship check 17)
- warn: [unreferenced] environment/app/registry/json-lattice.json is referenced nowhere else in the bundle (ship check 17)
- warn: [unreferenced] environment/app/registry/lru-cellar.json is referenced nowhere else in the bundle (ship check 17)
- warn: [unreferenced] environment/app/registry/mesh-http.json is referenced nowhere else in the bundle (ship check 17)
- warn: [unreferenced] environment/app/registry/quill-log.json is referenced nowhere else in the bundle (ship check 17)
- warn: [unreferenced] environment/app/registry/rivet-retry.json is referenced nowhere else in the bundle (ship check 17)
- warn: [unreferenced] environment/app/registry/spindle-tasks.json is referenced nowhere else in the bundle (ship check 17)
- warn: [unreferenced] environment/app/registry/tidy-args.json is referenced nowhere else in the bundle (ship check 17)
- sign-off (pass): The registry files are not referenced by basename because the loader reads the directory: registry.go:42 `paths, err := filepath.Glob(filepath.Join(dir, "*.json"))` with the default dir `/app/registry` (internal/cli/resolve.go `const defaultRegistry = "/app/registry"`). Each package is reached from the sample projects: ember-uuid, tidy-args by ledger-cli; mesh-http, quill-log, spindle-tasks, fern-config by storefront; lru-cellar, ansi-glyphs by batch-worker; json-lattice by fern-config; rivet-retry by batch-worker, ledger-cli and mesh-http (checked by parsing every pin.json and registry dependency map).

### 18 - No unused module that already implements the answer [SIGNED]
- sign-off (pass): Every Go package under environment/app/internal is imported on the path from cmd/pinwheel/main.go (cli -> semver, semrange, registry, manifest, resolve, lockfile); each file holds one piece (caret.go, tilde.go, xrange.go, hyphen.go, ...) and there is no second implementation: one definition each of `func caret(`, `func Compare(`, `func Resolve(`, `func choose(`, `func Encode(`. No dead helper already contains the fixed logic.

### 19 - Authoritative docs consistent with instruction.md [SIGNED]
- sign-off (pass): instruction.md:8 names semver 7.x with default options as the reference and ranges.md:5-7 says the same (`version 7.x, used with its defaults: strict parsing (loose: false) and includePrerelease: false`). The yanked-pin symptom matches resolution.md:29-32 (`An exact pin is a range that is a single full version, bare or with =`); the stale-package symptom matches resolution.md:49-50 (`Packages that are no longer required drop out of the selection`). cli.md matches the kept CLI; nothing in the docs conflicts with instruction.md.

### 20 - Non-authoritative docs hold no hidden graded rule [SIGNED]
- sign-off (pass): The only non-spec doc is environment/app/README.md: it has the build line `go build -o /usr/local/bin/pinwheel ./cmd/pinwheel`, an example invocation and the layout/doc index, and states no rule that the tests grade. docs/registry.md (listed in README.md:29) describes the registry and manifest file formats that the loaders already accept; no test depends on anything only stated there.

### 23 - Decoys are reachable, fair and not labelled [SIGNED]
- sign-off (n/a): No decoys were planted: every file in environment/ is part of the working program (`environment/app/internal/**/*.go`, `go.mod`), its spec (`environment/app/docs/*.md`), its default data (`registry/*.json`, `examples/*/pin.json`) or the Dockerfile; the check 17 warnings are the glob-loaded registry files, all reachable from the examples.

### 24 - solve.sh delta listed file by file [SIGNED]
- sign-off (pass): solve.sh rewrites 13 files by heredoc (MASTER_REPORT appendix `Solution delta`): version.go +2/-2 (reject leading-zero numeric prerelease ids), compare.go +15/-6 (numeric id order, longer list wins), comparator.go +1/-1 (`=` ignores build metadata), range.go +6/-2 (`||` without spaces, prerelease gate needs same triple), caret.go +13/-2 (left-most non-zero field), tilde.go +5/-2 (`~1`), xrange.go +2/-2 (`>1.2`, `<=1.2`), hyphen.go +6/-3 (partial upper end), resolver.go +17/-7 (replace the selection each round), constraints.go +1/-2 (override replaces constraints), yanked.go +10/-3 (bare exact pins), candidates.go +19/-10 (tie-break in lowest mode), lockfile.go +7/-3 (SetEscapeHTML(false)).

### 25 - Every touched file maps to a requested fix (no no-op delta) [SIGNED]
- sign-off (pass): Ablating any single file drops reward to 0 with specific failures (_reports/pinwheel-semver-range-repair/ablation.json for bundle d41992208d88a638): `u01-version-go` -> test_invalid_input_rejected, `u05-caret-go` -> test_caret_ranges, `u09-resolver-go` -> test_lock_drops_packages_no_longer_required, `u10-constraints-go` -> test_lock_applies_overrides, `u11-yanked-go` -> test_lock_yanked_releases, `u12-candidates-go` -> test_lock_prefer_lowest_and_ties, `u13-lockfile-go` -> six lock tests; every fixed behaviour is required by ranges.md, resolution.md or lockfile.md.

### 26 - No out-of-scope delta [SIGNED]
- sign-off (pass): The 13 heredocs change only the defect lines plus their doc comments (MASTER_REPORT appendix `Solution delta`, largest +19/-10 in candidates.go); the CLI files, registry/manifest loaders, docs, registry data and examples are not touched by solve.sh, and it ends with `gofmt -l`, `go vet`, `go test` and the documented `go build`.

### 27 - Reference output independently re-derived [SIGNED]
- sign-off (pass): Expected values were not produced by the Go solution: tests/cases.json was generated by `_reports/pinwheel-semver-range-repair/reference/gen_cases.js` calling node `semver@7.6.3` (tests/test_outputs.py:1 `expectations recorded from node-semver 7.6.3`), and the expected locks in tests/fixtures/expected/*.lock were computed by an independent JavaScript implementation of resolution.md/lockfile.md (`reference/gen_fixtures.js`, using node-semver for matching). The fixed Go tree was then checked against node-semver on 4000 random versions/ranges (`reference/fuzz.js` + `fuzz_check.py`) with 0 mismatches.

### 28 - Agent consensus vs reference outlier checked [SIGNED]
- sign-off (pass): There is no consensus against the reference: the three failing runs fail on different tests (run-01 test_lock_prefer_lowest_and_ties, run-02 build failure in xrange.go, run-04 test_invalid_input_rejected), and two runs (run-03, run-05) pass all 15 tests, agreeing with the reference. Where run-04 disagrees (`1.2.3-01` accepted) node-semver 7.6.3 rejects it and ranges.md:17 says numeric prerelease ids `must not have leading zeros`; where run-01 disagrees (`1.0.0+build.1` chosen) resolution.md:36-37 says the latest `published` wins `whichever way prefer points`.

### 30 - Each fix ablated alone produces test failures [PASS]

### 31 - Cold linux/amd64 oracle build runs cleanly [PASS]
- info: cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-27T09:51:55 (baselines.json)

### 33 - Guard-style tests are coupled to real behavior [SIGNED]
- sign-off (pass): The only guard is the source policy (tests/test_outputs.py:33-43): it fails on `^\s*require\b` in go.mod and on the quoted import paths `"(os/exec|syscall|unsafe|plugin|C)"` in non-test .go files, i.e. exactly what instruction.md:10 forbids. It skips `_test.go` files (:39). The shipped tree, the oracle tree and all five agent trees pass it: even run-02's setup error is raised by the next line, `assert build.returncode == 0, "go build failed:\n"`, not by the policy assertion, and the build right after the policy (:51-55) guarantees the checked source is what gets graded.

### 34 - NOP-passable guards coupled, not deleted [SIGNED]
- sign-off (pass): No test passes under NOP: oracle-nop-evidence/nop-1/test-stdout.txt and nop-2 report `15 failed`, each on a behavioural mismatch (16 `cases differ` assertions such as `9 of 26 cases differ`, 8 `expected exit 2 invalid version`, 4 `lock differs`), not on the source policy or the build.

### 35 - Assertions do what names/docstrings claim [SIGNED]
- sign-off (pass): Each docstring matches its body: satisfies tests call `_check_satisfies` on the group named in the docstring (tests/test_outputs.py:110-143), test_prerelease_precedence calls `_check_compare(pinwheel, "precedence")` (:148), test_invalid_input_rejected checks invalid versions/ranges and the valid controls (:151-172), each lock test compares one fixture's pin.lock byte for byte (:175-197), and test_resolution_failures checks the positive `small` lock plus exit 3, exact stderr and untouched sentinel lock (:200-216).

### 36 - Expected values never computed by agent-editable code [SIGNED]
- sign-off (pass): Expected values come only from tests/cases.json (tests/test_outputs.py:19) and tests/fixtures/expected/*.lock (:98), both copied in with tests/ at verification; the tests build pinwheel into /tmp/pinwheel-verify (:15-16) and never call code under /app to compute an expectation.

### 37 - Fixtures feeding expected values are not agent-editable [SIGNED]
- sign-off (pass): tests/cases.json, tests/fixtures/registry (21 packages) and tests/fixtures/projects are not in the image (Dockerfile only does `COPY app/ /app/`) and are mounted only at verification; resolve runs on a tmp_path copy (tests/test_outputs.py:92) with `--registry` pointing at the test fixtures (:93), so /app/registry and /app/examples do not affect grading.

### 38 - Held-out scenarios really change the graded outcome [SIGNED]
- sign-off (pass): The graded inputs are held out: tests/cases.json has 134 satisfies/compare rows plus 25 invalid/valid rows, and the lock tests use tests/fixtures/registry (21 packages) and 8 projects (prune, overrides, yanked, lowest, mixed, small, unsat, missing), none of which is in /app. The instruction names only 4 symptoms. Ablation shows each held-out group decides reward: e.g. `u06-tilde-go` -> test_tilde_ranges, `u08-hyphen-go` -> test_hyphen_ranges, `u12-candidates-go` -> test_lock_prefer_lowest_and_ties, `u13-lockfile-go` -> six lock tests, all `reward=0.0`.

### 39 - Exactness rules enforced literally (set equality) [SIGNED]
- sign-off (pass): Comparisons are exact: `(rc, out) != (0, expected)` for satisfies (tests/test_outputs.py:70) and compare (:83), `out == f"resolved {count} packages\n"` (:102), `actual == expected` for the full pin.lock (:107), `err.strip() == message` for resolution failures (:215); only the invalid-input check uses `startswith` on the documented `pinwheel: invalid version "V"` prefix (:158), matching cli.md:40-41 which specifies only that message.

### 40 - Test tolerances equal the stated tolerances [SIGNED]
- sign-off (n/a): There are no numeric tolerances: all checks are exact string/exit-code equality (tests/test_outputs.py:70, :83, :107, :215) and instruction.md states no tolerance.

### 43 - Test names describe what they check [SIGNED]
- sign-off (pass): Names match content (MASTER_REPORT appendix `Tests`): test_caret_ranges, test_tilde_ranges, test_partial_version_comparators, test_hyphen_ranges, test_prerelease_admission, test_union_and_operator_spacing, test_build_metadata_ignored, test_prerelease_precedence, test_invalid_input_rejected, test_lock_drops_packages_no_longer_required (fixture `prune`), test_lock_applies_overrides (`overrides`), test_lock_yanked_releases (`yanked`), test_lock_prefer_lowest_and_ties (`lowest`), test_lock_mixed_range_forms (`mixed`), test_resolution_failures (`unsat`, `missing`).

### 44 - Fail-closed tests carry a positive control [SIGNED]
- warn: tests/test_outputs.py:151 test_invalid_input_rejected asserts a rejection/non-zero exit with no positive control in the same function
- sign-off (pass): test_invalid_input_rejected does carry positive controls in the same function: tests/test_outputs.py:164-171 loop over `inv["valid_versions"]` (5 versions) and `inv["valid_ranges"]` (5 ranges) and fail if any is rejected (`valid version rejected`, `valid range rejected`). test_resolution_failures likewise starts with the positive `_check_lock(pinwheel, "small", tmp_path)` (:202). The oracle passes both (oracle-1..3 `15 passed`).

### 47 - description/keywords/authors/category/tags accurate [SIGNED]
- sign-off (pass): task.toml: description `Make a Go dependency resolver match npm semver 7 range semantics and its documented flat-lock resolution rules, including overrides, yanked pins and prerelease handling` matches the task; keywords go/semver/npm/dependency-resolution/lockfile and tags semver-ranges/prerelease-precedence/dependency-resolution/lockfile-format/differential-behavior describe it; category `debugging`; authors anonymous; languages ["go"]; codebase_size `small` (46 files under environment/); difficulty `medium` from the measured 2/5 (trajectories/SUMMARY.txt `[0, 0, 1, 0, 1]`).

### 51 - Every rubric line maps to a test or instruction [SIGNED]
- warn: rubric line "Agent reproduces a reported symptom by running pinwheel resolve on /app/examples or pinwheel compare" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent makes >1.2 start at 1.3.0 and <=1.2 include every 1.2.x release" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent accepts || with no surrounding whitespace" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent makes pin.lock carry <, > and & literally instead of as \u003c-style escapes" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent reruns an identical failing command three or more times in a row" maps to no test and no instruction sentence - confirm what grades it
- sign-off (pass): Each flagged line is graded: reproduce-first is a process criterion read from the trajectory, backed by the symptom list at instruction.md:3-6 and the sample projects in `/app/examples`; `>1.2`/`<=1.2` maps to test_partial_version_comparators (docstring `Operators applied to partial versions (>1.2, <=1, <1.2, 1.x, *)`) and ranges.md:67,70; `||` without whitespace maps to test_union_and_operator_spacing (`'||' with or without surrounding spaces`) and ranges.md:50; literal `<`, `>`, `&` maps to every byte-exact lock test (tests/test_outputs.py:107, `<root>` in each lock) and lockfile.md:9; the repeated-command line is a trajectory hygiene criterion.

### 53 - No mutually contradictory rubric lines [SIGNED]
- sign-off (pass): Read all 22 rubric.txt lines pairwise. The 17 positives each name a distinct fix or process step; the negatives forbid things no positive asks for: `invoke node or another program` vs the positive `checks the rebuilt pinwheel against node-semver`, which only compares outside pinwheel; `edits /app/docs, /app/registry or /app/examples` vs `reads /app/docs/...`, which only reads; `changes the documented command line` vs no positive touching the CLI; `reruns an identical failing command three or more times` vs `reproduces a reported symptom`, which needs one run. No single action earns a positive and a negative at once.

### 54 - No double-counted behavior [SIGNED]
- sign-off (pass): Each behaviour is scored once: caret, tilde, x-range, hyphen, prerelease gate, `||`, identifier precedence, build metadata and leading zeros are separate lines mapping to separate tests; the resolver lines (selection replacement, override, yanked pin, lowest tie-break, HTML escaping) map to separate fixtures (prune, overrides, yanked, lowest, all locks); the process lines grade reading docs before editing, reproducing before editing and verifying after the last fix, which are different moments.

### 70 - Each failing run's cause read from its own files [SIGNED]
- sign-off (pass): Read from each run's own verifier/test-stdout.txt and agent/trajectory.json: run-01 fails only test_lock_prefer_lowest_and_ties (`"version": "1.0.0+build.1"` instead of 1.0.0+build.2) because its candidates.go replace targeted a space-indented `if lowest {` block that does not exist in the tab-indented file, so the tie-break stayed buggy; run-02 fails all 15 at setup with `internal/semrange/xrange.go:3:8: "github.com/brightloom/pinwheel/internal/semver" imported and not used` (it never found the Go toolchain and never compiled); run-04 fails only test_invalid_input_rejected (`['satisfies', '1.2.3-01', '*']: expected exit 2 invalid version, got rc=0`) because its ParsePrerelease rewrite dropped the leading-zero check. run-03 and run-05 pass 15/15.

### 72 - NOT MET / negative verdicts cite that run's own evidence [SIGNED]
- sign-off (pass): Every NOT MET and negative line in the five rubric_score.txt files cites backticked fragments from that run's own trajectory.json/test-stdout.txt/pane, and master_check's citation scan reports no missing quote for any run (no [72] warning). Examples: run-01 cites its own `// Precedence points low, but ties always point to the latest`, run-02 its own `import \((.*?)\)` scanner, run-04 its own `// Numeric prerelease identifiers are unbounded by SemVer.`, run-05 its own `console.log('NO_SEMVER',e.message)`, run-03 its own `grep -H -E '"(quill-log|mesh-http|json-lattice|ember-uuid)"`. The five files differ run by run (totals 27, 2, 29, 28, 29).

### 73 - MET verdicts spot-checked against the trajectory [SIGNED]
- sign-off (pass): MET verdicts for fix lines were only given when the mapped test is PASSED in that run's own test-stdout.txt and the edit is quoted from its trajectory (master_check shows no [73] missing-quote warning). Spot checks: run-03 caret (`hi = semver.New(0, 0, p.patch+1)` + `PASSED ../tests/test_outputs.py::test_caret_ranges`), run-05 tie-break (`return !candidate.Published.Before(current.Published)` + test_lock_prefer_lowest_and_ties PASSED), run-04 table check after the fixes (`while IFS='|' read -r v r` over `1.3.0|>1.2`). run-02 gets no MET for any fix line because its tree never builds.

### 81 - Reward-hacking scan on every trajectory [SIGNED]
- info: [81] run-01: trajectory mentions grading paths ['/tests/'] — read and confirm no reads/writes (no agent command touched them - mention is in output/prose only)
- sign-off (pass): master_check scanned every command of all five trajectories: `grading-path commands: 0` for run-01..05 (MASTER_REPORT appendix `Runs`). The only hit is prose in run-01 step 39 (`Then run gofmt/tests/build and CLI smoke tests`), not a command. No run reads or writes /tests, test_outputs.py, ctrf.json, reward.txt, /logs/verifier or solution/; all changes are Go source edits followed by go build/test; run_k reported `truncated=0` for every trial and each trajectory ends in mark_task_complete. run-05 downloaded the Go toolchain from go.dev, which allow_internet = true permits.

### 83 - Difficulty comes from genuine reasoning, source classified [SIGNED]
- sign-off (pass): Source classified as genuine reasoning/engineering breadth: 13 defects across semver parsing/precedence, five range desugarings, prerelease admission, a round-based resolver, override/yanked/tie-break rules and the lock encoder; only 4 are named by symptom and the rest must be found by auditing against ranges.md, resolution.md and lockfile.md (instruction.md:8 `I doubt that's all of it`). Every rule has an explicit doc sentence or table row (e.g. ranges.md:17 leading zeros, resolution.md:36-37 tie-break, lockfile.md:9 escaping). Measured 2/5 (Medium); the three failures are distinct real mistakes (no-op edit, uncompiled tree, missed doc rule), not a shared trap. No obscurity, decoys, contradictions or compliance walls.

## Appendix - Instruction paths (check 7)

- `/app` (instruction.md:1) -> environment/app
- `/app/examples` (instruction.md:1) -> environment/app/examples
- `/app/docs/ranges.md` (instruction.md:8) -> environment/app/docs/ranges.md
- `/app/docs/resolution.md` (instruction.md:8) -> environment/app/docs/resolution.md
- `/app/docs/lockfile.md` (instruction.md:8) -> environment/app/docs/lockfile.md
- `/app/docs/cli.md` (instruction.md:8) -> environment/app/docs/cli.md
- `/app/cmd/pinwheel` (instruction.md:10) -> environment/app/cmd/pinwheel

## Appendix - Stated constants (checks 6, 40)

- instruction.md:6 `-1` -> present in tests/

## Appendix - Solution delta (checks 24-26, 30)

- `/app/internal/semver/version.go` via heredoc at solve.sh:7-194 -> environment/app/internal/semver/version.go: +2 / -2 lines
- `/app/internal/semver/compare.go` via heredoc at solve.sh:198-266 -> environment/app/internal/semver/compare.go: +15 / -6 lines
- `/app/internal/semrange/comparator.go` via heredoc at solve.sh:269-341 -> environment/app/internal/semrange/comparator.go: +1 / -1 lines
- `/app/internal/semrange/range.go` via heredoc at solve.sh:345-496 -> environment/app/internal/semrange/range.go: +6 / -2 lines
- `/app/internal/semrange/caret.go` via heredoc at solve.sh:499-527 -> environment/app/internal/semrange/caret.go: +13 / -2 lines
- `/app/internal/semrange/tilde.go` via heredoc at solve.sh:530-548 -> environment/app/internal/semrange/tilde.go: +5 / -2 lines
- `/app/internal/semrange/xrange.go` via heredoc at solve.sh:551-595 -> environment/app/internal/semrange/xrange.go: +2 / -2 lines
- `/app/internal/semrange/hyphen.go` via heredoc at solve.sh:598-619 -> environment/app/internal/semrange/hyphen.go: +6 / -3 lines
- `/app/internal/resolve/resolver.go` via heredoc at solve.sh:622-682 -> environment/app/internal/resolve/resolver.go: +17 / -7 lines
- `/app/internal/resolve/constraints.go` via heredoc at solve.sh:685-766 -> environment/app/internal/resolve/constraints.go: +1 / -2 lines
- `/app/internal/resolve/yanked.go` via heredoc at solve.sh:769-795 -> environment/app/internal/resolve/yanked.go: +10 / -3 lines
- `/app/internal/resolve/candidates.go` via heredoc at solve.sh:799-854 -> environment/app/internal/resolve/candidates.go: +19 / -10 lines
- `/app/internal/lockfile/lockfile.go` via heredoc at solve.sh:857-957 -> environment/app/internal/lockfile/lockfile.go: +7 / -3 lines

## Appendix - Tests (checks 35, 43)

- tests/test_outputs.py:110 test_caret_ranges - Caret ranges, including 0.x and 0.0.x versions, partials and prereleases, match node-semver.
- tests/test_outputs.py:115 test_tilde_ranges - Tilde ranges (~, ~>, major-only and major.minor forms) match node-semver.
- tests/test_outputs.py:120 test_partial_version_comparators - Operators applied to partial versions (>1.2, <=1, <1.2, 1.x, *) match node-semver.
- tests/test_outputs.py:125 test_hyphen_ranges - Hyphen ranges with full and partial ends match node-semver.
- tests/test_outputs.py:130 test_prerelease_admission - Prereleases only match a set naming a prerelease of the same major.minor.patch.
- tests/test_outputs.py:135 test_union_and_operator_spacing - '||' with or without surrounding spaces, spaces after operators and the empty range.
- tests/test_outputs.py:140 test_build_metadata_ignored - Build metadata affects neither range matching nor compare output.
- tests/test_outputs.py:146 test_prerelease_precedence - compare orders prereleases by SemVer 2.0.0 precedence (numeric ids, longer sets, v prefix).
- tests/test_outputs.py:151 test_invalid_input_rejected - Strictly invalid versions and ranges exit 2 with the documented message; valid ones are accepted.
- tests/test_outputs.py:175 test_lock_drops_packages_no_longer_required - Packages no longer required after a later round downgrades a release are dropped from the lock.
- tests/test_outputs.py:180 test_lock_applies_overrides - An override replaces the dependents' ranges and never adds a package by itself.
- tests/test_outputs.py:185 test_lock_yanked_releases - Yanked releases are skipped unless an exact pin (bare or '=') names them.
- tests/test_outputs.py:190 test_lock_prefer_lowest_and_ties - prefer=lowest picks lowest releases; equal-precedence ties go to latest published, then file order.
- tests/test_outputs.py:195 test_lock_mixed_range_forms - A project using caret, tilde, hyphen, partial, union, prerelease and build-metadata ranges locks correctly.
- tests/test_outputs.py:200 test_resolution_failures - Unsatisfiable and unknown packages exit 3 with the documented message and leave pin.lock alone.

## Appendix - Rubric map (checks 51, 54)

- `Agent reads /app/docs/ranges.md and /app/docs/resolution.md before editing the range or re` (+2) -> test `test_caret_ranges` (1 shared words); instruction.md:8 (2)
- `Agent reproduces a reported symptom by running pinwheel resolve on /app/examples or pinwhe` (+1) -> test `test_partial_version_comparators` (1 shared words); instruction.md:1 (1)
- `Agent makes caret ranges keep the left-most non-zero field so ^0.2.3 stops below 0.3.0 and` (+2) -> test `test_caret_ranges` (2 shared words); instruction.md:1 (1)
- `Agent makes a major-only tilde such as ~1 cover every 1.x release` (+1) -> test `test_tilde_ranges` (2 shared words); instruction.md:1 (0)
- `Agent makes >1.2 start at 1.3.0 and <=1.2 include every 1.2.x release` (+1) -> test `test_caret_ranges` (1 shared words); instruction.md:1 (0)
- `Agent makes a partial upper end of a hyphen range cover every version it matches` (+1) -> test `test_caret_ranges` (4 shared words); instruction.md:1 (1)
- `Agent admits a prerelease only when the set has a prerelease comparator with the same majo` (+3) -> test `test_prerelease_admission` (4 shared words); instruction.md:1 (0)
- `Agent accepts || with no surrounding whitespace` (+1) -> test `test_union_and_operator_spacing` (1 shared words); instruction.md:1 (0)
- `Agent compares numeric prerelease identifiers numerically and ranks a longer identifier li` (+2) -> test `test_prerelease_precedence` (5 shared words); instruction.md:1 (0)
- `Agent makes exact comparators ignore build metadata` (+1) -> test `test_build_metadata_ignored` (4 shared words); instruction.md:5 (1)
- `Agent rejects numeric prerelease identifiers that have leading zeros` (+1) -> test `test_prerelease_precedence` (2 shared words); instruction.md:1 (0)
- `Agent replaces the selection each round so packages that are no longer required drop out o` (+3) -> test `test_lock_drops_packages_no_longer_required` (5 shared words); instruction.md:1 (1)
- `Agent makes an override replace the dependents' ranges instead of being combined with them` (+2) -> test `test_lock_applies_overrides` (4 shared words); instruction.md:1 (1)
- `Agent treats a bare full version as an exact pin that makes a yanked release eligible` (+2) -> test `test_lock_yanked_releases` (4 shared words); instruction.md:5 (1)
- `Agent breaks equal-precedence ties by latest published time and then file order under pref` (+2) -> test `test_lock_prefer_lowest_and_ties` (8 shared words); instruction.md:1 (0)
- `Agent makes pin.lock carry <, > and & literally instead of as \u003c-style escapes` (+2) -> test `test_lock_drops_packages_no_longer_required` (1 shared words); instruction.md:1 (1)
- `Agent checks the rebuilt pinwheel against node-semver or the ranges.md table after its fix` (+3) -> test `test_caret_ranges` (3 shared words); instruction.md:8 (2)
- `Agent makes pinwheel invoke node or another program, or imports os/exec, syscall, unsafe, ` (-5) -> test `test_caret_ranges` (1 shared words); instruction.md:10 (5)
- `Agent special-cases the packages, versions or ranges named in the instruction or the examp` (-5) -> test `test_caret_ranges` (2 shared words); instruction.md:1 (2)
- `Agent edits /app/docs, /app/registry or /app/examples to match the current behavior instea` (-3) -> test `test_caret_ranges` (1 shared words); instruction.md:8 (2)
- `Agent changes the documented command line, output or exit codes` (-3) -> test `test_invalid_input_rejected` (2 shared words); instruction.md:10 (3)
- `Agent reruns an identical failing command three or more times in a row` (-1) -> test `test_caret_ranges` (0 shared words); instruction.md:10 (1)

## Appendix - Runs (checks 70, 81)

- run-01: 42 steps, grading-path commands: 0, failed tests: test_lock_prefer_lowest_and_ties
- run-02: 42 steps, grading-path commands: 0, failed tests: test_caret_ranges, test_tilde_ranges, test_partial_version_comparators, test_hyphen_ranges, test_prerelease_admission, test_union_and_operator_spacing, test_build_metadata_ignored, test_prerelease_precedence, test_invalid_input_rejected, test_lock_drops_packages_no_longer_required, test_lock_applies_overrides, test_lock_yanked_releases, test_lock_prefer_lowest_and_ties, test_lock_mixed_range_forms, test_resolution_failures
- run-03: 16 steps, grading-path commands: 0, failed tests: none
- run-04: 43 steps, grading-path commands: 0, failed tests: test_invalid_input_rejected
- run-05: 51 steps, grading-path commands: 0, failed tests: none

## Appendix - Ablation (check 30)

- `/app/internal/semver/version.go` removed -> reward 0.0, failing: test_invalid_input_rejected
- `/app/internal/semver/compare.go` removed -> reward 0.0, failing: test_prerelease_precedence, test_lock_mixed_range_forms
- `/app/internal/semrange/comparator.go` removed -> reward 0.0, failing: test_build_metadata_ignored, test_lock_mixed_range_forms
- `/app/internal/semrange/range.go` removed -> reward 0.0, failing: test_prerelease_admission, test_union_and_operator_spacing, test_invalid_input_rejected, test_lock_mixed_range_forms
- `/app/internal/semrange/caret.go` removed -> reward 0.0, failing: test_caret_ranges, test_lock_mixed_range_forms, test_resolution_failures
- `/app/internal/semrange/tilde.go` removed -> reward 0.0, failing: test_tilde_ranges, test_lock_mixed_range_forms
- `/app/internal/semrange/xrange.go` removed -> reward 0.0, failing: test_partial_version_comparators, test_lock_mixed_range_forms
- `/app/internal/semrange/hyphen.go` removed -> reward 0.0, failing: test_hyphen_ranges, test_lock_mixed_range_forms
- `/app/internal/resolve/resolver.go` removed -> reward 0.0, failing: test_lock_drops_packages_no_longer_required
- `/app/internal/resolve/constraints.go` removed -> reward 0.0, failing: test_lock_applies_overrides
- `/app/internal/resolve/yanked.go` removed -> reward 0.0, failing: test_lock_yanked_releases
- `/app/internal/resolve/candidates.go` removed -> reward 0.0, failing: test_lock_prefer_lowest_and_ties
- `/app/internal/lockfile/lockfile.go` removed -> reward 0.0, failing: test_lock_drops_packages_no_longer_required, test_lock_applies_overrides, test_lock_yanked_releases, test_lock_prefer_lowest_and_ties, test_lock_mixed_range_forms, test_resolution_failures
