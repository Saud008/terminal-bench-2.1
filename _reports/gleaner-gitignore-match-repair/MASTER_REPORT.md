# Master Ship Checklist - gleaner-gitignore-match-repair

Bundle sha `d3acf08ebc8fbcd3`, generated 2026-09-27 10:57. FAIL 0, STALE 0, REVIEW 0, MANUAL 0, SIGNED 41, PASS 46

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
| 8 | A | Output schema exactness in prose matches the tests | assist | **SIGNED** | instruction.md:8 exactness rule "gleaner is meant to decide exactly like git: `gleaner list` should print what `git ls-f |
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
| 31 | C | Cold linux/amd64 oracle build runs cleanly | auto | **PASS** | cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-27T10:27:09 (baselines.json) |
| 32 | D | Zero individual tests pass under NOP | auto | **PASS** |  |
| 33 | D | Guard-style tests are coupled to real behavior | assist | **SIGNED** |  |
| 34 | D | NOP-passable guards coupled, not deleted | manual | **SIGNED** |  |
| 35 | D | Assertions do what names/docstrings claim | assist | **SIGNED** |  |
| 36 | D | Expected values never computed by agent-editable code | assist | **SIGNED** |  |
| 37 | D | Fixtures feeding expected values are not agent-editable | assist | **SIGNED** |  |
| 38 | D | Held-out scenarios really change the graded outcome | manual | **SIGNED** |  |
| 39 | D | Exactness rules enforced literally (set equality) | assist | **SIGNED** | instruction.md:8 "gleaner is meant to decide exactly like git: `gleaner list` should print what `git ls-files --others - |
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
| 51 | F | Every rubric line maps to a test or instruction | assist | **SIGNED** | rubric line "Agent changes the documented command line, output format or exit codes" maps to no test and no instruction  |
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
| 81 | G | Reward-hacking scan on every trajectory | assist | **SIGNED** |  |
| 82 | G | Evidence regenerated atomically after the last k=5 | auto | **PASS** |  |
| 83 | I | Difficulty comes from genuine reasoning, source classified | manual | **SIGNED** |  |
| 84 | I | Delivery structure exact, no junk | auto | **PASS** |  |
| 85 | I | Final stb / personal-path scrub across the whole bundle | auto | **PASS** |  |

## Findings and sign-offs

### 0 - Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens [SIGNED]
- sign-off (pass): instruction.md is 10 lines, about 220 words (well under 1500 tokens), written as a build-farm bug report (instruction.md:1 `the snapshots keep disagreeing with what git shows on a developer's machine`). Every absolute path is in backticks: `/app` (instruction.md:1), `/app/docs` (instruction.md:8), `/app/Cargo.toml` and `/app/docs/cli.md` (instruction.md:10). The graded outputs are named: `gleaner list` must print what `git ls-files --others --exclude-standard` prints and `gleaner check` what `git check-ignore -v -n` prints (instruction.md:8).

### 1 - Every stated requirement is exercised by a test [SIGNED]
- sign-off (pass): Each stated item is graded. build/ at every depth -> test_directory_only_patterns (tests/test_outputs.py:139); Windows-saved .gitignore -> test_file_encodings (:124); !keep.tmp in a subdirectory -> test_per_directory_precedence (:164); ! file under an ignored directory -> test_reinclude_under_excluded_directory (:159); `There's probably more` plus list/check parity with git (instruction.md:8) -> the remaining groups and 30 mixed_trees cases recorded from git (tests/cases.json); docs as spec -> every group follows patterns.md/sources.md/cli.md; std-only, no unsafe/FFI, no running programs -> _source_policy_problems (:49-63) and git hidden by _hide_reference_tools (:26-32); plain cargo build --release -> the session fixture builds with cargo (:72-76).

### 2 - Every requirement a test enforces is stated [SIGNED]
- sign-off (pass): Everything enforced is stated. list output and exit 0, check stdout and exit status (0/1) come from `/app/docs/cli.md`, which instruction.md:10 says to keep (cli.md:33 `Exit status 0.`, cli.md:68 `Exit status: 0 if at least one PATH is ignored`). Pattern and source rules are in patterns.md and sources.md, which instruction.md:8 makes the spec. The Cargo.lock/unsafe/extern/#[link]/Command policy (tests/test_outputs.py:35-63) enforces instruction.md:10 `no dependencies in /app/Cargo.toml, no unsafe or FFI, and don't run git or any other program from gleaner`. The `--offline --locked` build (:73) matches `no dependencies`: with no crates there is nothing to fetch. Unseen trees are announced (instruction.md:8 `It will be run against other trees, patterns and configs than the ones mentioned here.`).

### 3 - No implementation-step ('how') sentences [SIGNED]
- sign-off (pass): instruction.md gives symptoms (lines 3-6), the reference behaviour and spec (line 8) and constraints (line 10). No sentence names a source file, function or algorithm to change. The only approach directive is `treat those docs as the spec and fix the code, not the docs` (instruction.md:8), which is an outcome rule.

### 4 - Interface contracts named in the prompt are really graded [SIGNED]
- sign-off (pass): The interfaces named are `gleaner list`, `gleaner check` and the formats from `/app/docs/cli.md` (instruction.md:8, 10). tests/test_outputs.py:112 runs `list` and requires `(rc, out) == (0, case["list"])`. tests/test_outputs.py:115-116 runs `check -- PATH...` and requires rc and stdout to equal the recorded `check_rc`/`check` exactly. Those follow cli.md:4-5 (`gleaner [--root DIR] list`, `gleaner [--root DIR] check [--] PATH...`) and the `SOURCE:LINE:PATTERN<TAB>PATH` line format at cli.md:41.

### 6 - Stated constants match tests byte for byte [SIGNED]
- sign-off (pass): The only literals in instruction.md are the pattern examples `build/`, `!keep.tmp`, `*.tmp` and `!` (instruction.md:3-6) and the git commands (instruction.md:8). The tests compare against git's own output recorded in tests/cases.json, so no constant is restated by hand. The directory_only_patterns, per_directory_precedence and reinclude groups use those same pattern shapes (e.g. `build/`, `*.tmp` with `!keep.tmp`).

### 8 - Output schema exactness in prose matches the tests [SIGNED]
- warn: instruction.md:8 exactness rule "gleaner is meant to decide exactly like git: `gleaner list` should print what `git ls-files --others --exclude-standard`" but tests/ show no set/list equality assertion
- sign-off (pass): Exactness is enforced as literal whole-output equality. tests/test_outputs.py:113 `if (rc, out) != (0, case["list"]):` compares the complete list stdout (set and order) with the string git printed. tests/test_outputs.py:117 `if (rc, out) != (case["check_rc"], case["check"]):` compares the complete check stdout. The expected strings are git's own output (test_outputs.py:1-4), so `exactly like git` (instruction.md:8) is checked byte for byte. The scanner just didn't recognise tuple equality as a set/list assertion.

### 9 - No self-contradiction between sentences [SIGNED]
- sign-off (pass): Read sentence by sentence: the symptom list, `There's probably more.`, the git-parity sentence, the docs-as-spec sentence, the unseen-trees sentence and the constraints paragraph are consistent. The one place gleaner deliberately differs from git is check's exit status: cli.md:69 says `This differs from git, which also counts negated matches when -v is given`. instruction.md:8 only asks check to print what git prints (stdout), and instruction.md:10 keeps cli.md, so there is no conflict.

### 10 - Prompt does not narrate each planted defect's mechanism [SIGNED]
- sign-off (pass): instruction.md:3-6 only give observable results (`only drops the top-level build directory`, `seems to be ignored completely`, `doesn't bring back that directory's keep.tmp`, `shows up in the snapshot, git leaves it out`). None names a mechanism (slash test before stripping the trailing slash, BOM/CR handling, stack iteration order, negation overriding an excluded parent). The other defects are not mentioned at all: trailing-space trimming, the escaped \! leader, anchoring relative to the .gitignore directory, ** component rules, bracket negation, info/exclude order, the XDG default, config key case and list byte order.

### 11 - Every environment file is required [SIGNED]
- sign-off (pass): All 30 files under environment/ are used. The Dockerfile builds the image (`cargo build --release --offline`) and .dockerignore keeps junk out of the context. Cargo.toml and Cargo.lock define the crate, and the Cargo.lock package list is checked by tests/test_outputs.py:51-54. The 22 .rs files are compiled: lib.rs declares cli, config, error, ignore, report and walk, and each mod.rs declares its submodules. README.md is the project readme. docs/cli.md, patterns.md and sources.md are the spec named in instruction.md:8/10. Ship check 17 (dead/orphaned files) passes.

### 13 - No comments echoing instruction or rubric text [SIGNED]
- sign-off (pass): Grep of every `//` comment in environment/app/src shows only neutral descriptions of what the code does, e.g. lines.rs:10 `Splits file contents on \n, dropping blank lines and # comments.`, stack.rs:42 `Combines the decision inherited from an excluded parent directory with the path's own last matching pattern.`, order.rs:1 `Sorts listed paths directory by directory`. None restates instruction.md sentences or rubric wording, and the automatic check 12 (BUG/FIXME/planted comments) passes.

### 14 - No lore/notes doc indexing the planted defects [SIGNED]
- sign-off (pass): environment/app has no notes, changelog or history file. README.md only describes purpose, build and layout (README.md:20 `Layout: src/cli (argument handling and the two commands), src/ignore ...`). docs/*.md describe intended behaviour and never mention defects.

### 16 - No names that mislabel behavior [SIGNED]
- sign-off (pass): Names match behaviour: `split` splits lines, `trim_trailing_spaces` trims, `parse_line` parses, `last_match` finds the last matching pattern, `wildmatch` and `bracket` match globs and sets, `classify`/`resolve`/`check_path` combine sources, `default_excludes_file` returns the default path, `sort_paths` sorts. Doc comments on defective functions describe what the shipped code really does (order.rs:1 `comparing one path component at a time`, parse.rs:15 `Removes trailing whitespace.`) rather than claiming the correct behaviour, so nothing is mislabelled.

### 18 - No unused module that already implements the answer [SIGNED]
- sign-off (pass): There is one matcher (ignore/wildmatch.rs + charclass.rs), one parser (ignore/parse.rs), one source combiner (ignore/stack.rs) and one sorter (walk/order.rs). Every module is reachable from main.rs through cli::run. No alternate or disabled implementation exists: `grep -rn "fn wildmatch\|fn sort_paths\|fn trim_trailing_spaces" src` gives one definition each.

### 19 - Authoritative docs consistent with instruction.md [SIGNED]
- sign-off (pass): The docs state the rules behind every reported symptom. patterns.md:27 `A trailing / makes the pattern match directories only. It is removed before the rest of these rules are applied.` (build/ at any depth). patterns.md:9-11 BOM and CR handling (Windows editor). sources.md:8-9 `A deeper file overrides a shallower one.` (!keep.tmp). sources.md:22 `Once a directory is excluded, nothing inside it can be re-included` (! under an ignored directory). cli.md:13 `Output is exactly what git prints for the same tree` matches instruction.md:8, and patterns.md:62 keeps only the ** behaviour that git 2.39 and 2.53 share.

### 20 - Non-authoritative docs hold no hidden graded rule [SIGNED]
- sign-off (pass): The only non-spec doc is README.md. It states purpose, a build/usage example (README.md:9-11), `It is plain Rust on the standard library.` (also instruction.md:10) and the layout. It holds no pattern, source or output rule that is not already in docs/cli.md, patterns.md or sources.md.

### 23 - Decoys are reachable, fair and not labelled [SIGNED]
- sign-off (pass): No deliberate decoys and no labels (README.md:20-23 only lists the layout, `src/walk (tree walk and output order), src/report (output lines)`). The correct, unchanged code (walk/tree.rs, report/mod.rs, cli/*, the value-unquoting half of config/gitconfig.rs, ignore/sources.rs read_optional) is reachable and behaves as the docs say. The oracle leaves it untouched and passes 15/15 (oracle-nop-evidence/oracle-1/ctrf.json). Agents that also refactored tree.rs (run-04, run-05) still passed, so touching it is neither required nor punished.

### 24 - solve.sh delta listed file by file [SIGNED]
- sign-off (pass): solve.sh rewrites exactly 10 files, each preceded by a one-line comment (solve.sh:6, 36, 108, 189, 339, 445, 572, 646, 675, 846): src/ignore/lines.rs (+9/-3), parse.rs (+31/-12), pattern.rs (+13/-4), wildmatch.rs (+29/-9), charclass.rs (+14/-6), stack.rs (+6/-6), sources.rs (+3/-3), src/config/paths.rs (+4/-1), gitconfig.rs (+7/-2), src/walk/order.rs (+4/-3), per the MASTER_REPORT solution-delta appendix. It then runs `cargo build --release --offline`.

### 25 - Every touched file maps to a requested fix (no no-op delta) [SIGNED]
- sign-off (pass): Per-file ablation (_reports/gleaner-gitignore-match-repair/ablation.json): reverting any one file drops the reward to 0. lines.rs -> test_file_encodings, test_check_line_numbers; parse.rs -> test_trailing_spaces, test_escaped_leading_characters, test_directory_only_patterns; pattern.rs -> test_anchoring; wildmatch.rs -> test_double_star; charclass.rs -> test_bracket_expressions; stack.rs -> test_reinclude_under_excluded_directory, test_per_directory_precedence; sources.rs -> test_tree_wide_sources; paths.rs -> test_default_excludes_file; gitconfig.rs -> test_config_spelling; order.rs -> test_list_order. Each maps to a doc rule behind instruction.md:8 `decide exactly like git`.

### 26 - No out-of-scope delta [SIGNED]
- sign-off (pass): The delta is limited to the 10 defect files, with small per-file changes (largest parse.rs +31/-12). No doc, test, Cargo.toml, CLI or report file is touched: `grep -n "cat > " solution/solve.sh` lists only src/ignore/*, src/config/paths.rs, src/config/gitconfig.rs and src/walk/order.rs. The output format and exit codes are unchanged, as the oracle's byte-exact pass shows (oracle-nop-evidence/oracle-1/reward.txt = 1).

### 27 - Reference output independently re-derived [SIGNED]
- sign-off (pass): Expected outputs are not computed by the reference solution. They were recorded from real git in two versions. tests/cases.json was recorded with git 2.39.5 in the dev container, then re-recorded now with WSL git 2.53.0: `wsl bash _reports/gleaner-gitignore-match-repair/rerecord253.sh` printed `git version 2.53.0`, `git 2.53 re-recording IDENTICAL to tests/cases.json`, and matching sha prefixes `bc99cef5bf26184f` for both files. The corrected binary also fuzzes to 0 mismatches against git (fuzz.py; 3000 trees on 2.39, 2000+ on 2.53).

### 28 - Agent consensus vs reference outlier checked [SIGNED]
- sign-off (pass): 3 of 5 runs (run-02, run-04, run-05) independently reproduce all 74 recorded outputs (reward 1). The two failures (run-01, run-03) disagree only where their `**/` handling lets a leading or middle globstar resume mid-component. The verifier shows `.gitignore:1:a/**/b<TAB>a/xb` where git prints `::<TAB>a/xb`, and patterns.md:59-60 says `/**/ matches zero or more directories, so a/**/b matches a/b, a/x/b and a/x/y/b`. The reference agrees with git, not with the outliers.

### 31 - Cold linux/amd64 oracle build runs cleanly [PASS]
- info: cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-27T10:27:09 (baselines.json)

### 33 - Guard-style tests are coupled to real behavior [SIGNED]
- sign-off (pass): The only guards (source policy, git hidden, build) live in the session fixture (tests/test_outputs.py:66-78). Every test then compares real list/check output with git's recording (:108-121). A guard can only make tests fail, never pass: an empty or stubbed gleaner fails all 15 tests (oracle-nop-evidence/nop-1/ctrf.json, 15 failed).

### 34 - NOP-passable guards coupled, not deleted [SIGNED]
- sign-off (pass): No test passes under NOP: nop-1 and nop-2 each report 15 failed / 0 passed (oracle-nop-evidence/nop-1/ctrf.json, nop-2/ctrf.json), and checks 32 and 60 pass. There is no standalone guard test that NOP could pass: the policy assert `assert not problems` sits inside the session fixture (tests/test_outputs.py:70), not in a test of its own.

### 35 - Assertions do what names/docstrings claim [SIGNED]
- sign-off (pass): Each test_X calls _check_group(gleaner, "X") on the tests/cases.json group of the same name (tests/test_outputs.py:124-196). The groups hold exactly the scenarios the docstrings name, e.g. test_bracket_expressions (:154) `^ and ! negation, a leading ] member, ranges and POSIX classes`, and test_list_order (:184) `punctuation below / sorts ahead of a subdirectory` (the first list_order tree expects `a-b`, then `a.b/c`, `a/b-c`, `a/b.d`, `a/b/c`, then `a0`). _check_group asserts full list and check equality (:113, :117).

### 36 - Expected values never computed by agent-editable code [SIGNED]
- sign-off (pass): Expected values are the literal `list`, `check` and `check_rc` fields of tests/cases.json, recorded from git (tests/test_outputs.py:1-4, :23). Nothing under /app is imported or run to compute them. /app code only produces the actual output, via the freshly built binary (:72-78).

### 37 - Fixtures feeding expected values are not agent-editable [SIGNED]
- sign-off (pass): tests/cases.json and test_outputs.py are copied in by the harness at verification time and are not in the image. Check 22 (Dockerfile never copies solution/ or tests/) passes, and the Dockerfile only has `COPY app/ /app/`. Case trees are materialised fresh under /tmp/gleaner-case for every case (tests/test_outputs.py:87-99), so nothing the agent leaves on disk feeds them.

### 38 - Held-out scenarios really change the graded outcome [SIGNED]
- sign-off (pass): instruction.md:8 announces `other trees, patterns and configs than the ones mentioned here`. 70 of the 74 cases use trees and patterns not in the prompt, including 30 random mixed_trees. They decide the outcome: run-01 and run-03 fixed all four reported symptoms (their test_directory_only_patterns, test_file_encodings, test_per_directory_precedence and test_reinclude_under_excluded_directory passed) yet scored 0 because of `FAILED ../tests/test_outputs.py::test_double_star` and test_mixed_trees.

### 39 - Exactness rules enforced literally (set equality) [SIGNED]
- warn: instruction.md:8 "gleaner is meant to decide exactly like git: `gleaner list` should print what `git ls-files --others --exclude-standard`" - no literal equality enforcement found in tests/
- sign-off (pass): Enforced literally, and stricter than set equality. tests/test_outputs.py:113 `if (rc, out) != (0, case["list"]):` requires the whole list stdout (membership and order) to equal git's output string. tests/test_outputs.py:117 does the same for check stdout plus exit code, and :121 fails the test on any mismatch.

### 40 - Test tolerances equal the stated tolerances [SIGNED]
- sign-off (n/a): No numeric output and no tolerance anywhere. All comparisons are exact string/int equality (tests/test_outputs.py:113, :117), matching instruction.md:8 `exactly like git`.

### 43 - Test names describe what they check [SIGNED]
- sign-off (pass): Names equal the rule each group covers: test_file_encodings, test_trailing_spaces, test_escaped_leading_characters, test_directory_only_patterns, test_anchoring, test_double_star, test_bracket_expressions, test_reinclude_under_excluded_directory, test_per_directory_precedence, test_tree_wide_sources, test_default_excludes_file, test_config_spelling, test_list_order, test_check_line_numbers, test_mixed_trees (tests/test_outputs.py:124-196). The failing ablations line up with the names (ablation.json: charclass.rs -> test_bracket_expressions, order.rs -> test_list_order).

### 44 - Fail-closed tests carry a positive control [SIGNED]
- sign-off (pass): Every group mixes paths git ignores and paths it keeps, so tests assert positive as well as negative outcomes. check_rc is 0 in some cases and 1 in others (e.g. test_escaped_leading_characters has `::<TAB>` no-match lines alongside matches), and list must contain the non-ignored files. The oracle passes 15/15 (oracle-1..3), which shows the assertions are satisfiable, and NOP fails 15/15.

### 47 - description/keywords/authors/category/tags accurate [SIGNED]
- sign-off (pass): task.toml:4 description `Make a Rust gitignore evaluator list untracked files and explain ignore decisions exactly as git ls-files and git check-ignore do` matches instruction.md:8. keywords `gitignore, wildmatch, rust, git, glob-matching` and tags `gitignore, wildmatch, pattern-precedence, core-excludesfile, differential-behavior` describe the code and tests. category = "debugging" (task.toml:7, 18) fits a bug-report repair. difficulty = "medium" matches the measured 3/5. languages = ["rust"], codebase_size = "small" (22 .rs files). [[task.authors]] and the metadata author fields are the pool's anonymous values.

### 51 - Every rubric line maps to a test or instruction [SIGNED]
- warn: rubric line "Agent changes the documented command line, output format or exit codes" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent reruns an identical failing command three or more times in a row" maps to no test and no instruction sentence - confirm what grades it
- sign-off (pass): `Agent changes the documented command line, output format or exit codes` maps to instruction.md:10 `Keep the command line and output formats from /app/docs/cli.md`. It is also enforced by every test, since the tests invoke `list` and `check --` and compare stdout and exit codes (tests/test_outputs.py:112-117); the rubric line grades the process from the trajectory. `Agent reruns an identical failing command three or more times in a row` is a process-hygiene negative graded only from the trajectory, the standard rubric pattern; each run's rubric_score.txt cites commands from its own trajectory for it.

### 53 - No mutually contradictory rubric lines [SIGNED]
- sign-off (pass): The 17 positive lines each cover a different rule or phase (docs first, reproduce before editing, one line per rule, verify after fixing). The 5 negatives forbid things no positive requires: running programs or adding crates/unsafe, special-casing prompt paths, editing docs, changing the CLI, looping on a failing command. Criterion 2 (reproduce before editing) and criterion 17 (compare after fixes) cover different phases and can both be met, as run-02 shows (trajectories/run-02/rubric_score.txt:23 `Total | 30 / 30`). The negative at rubric.txt:20 `Agent edits /app/docs to match the current behavior instead of fixing the code` agrees with instruction.md:8 `fix the code, not the docs`.

### 54 - No double-counted behavior [SIGNED]
- sign-off (pass): Each rule-level positive maps to one distinct test group (MASTER_REPORT rubric map): BOM+CR -> test_file_encodings, line numbers -> test_check_line_numbers, trailing spaces -> test_trailing_spaces, \! -> test_escaped_leading_characters, trailing slash -> test_directory_only_patterns, relative anchoring -> test_anchoring, ** -> test_double_star, brackets -> test_bracket_expressions, deeper .gitignore -> test_per_directory_precedence, excluded dir -> test_reinclude_under_excluded_directory, info/exclude -> test_tree_wide_sources, XDG -> test_default_excludes_file, key case -> test_config_spelling, byte sort -> test_list_order. The three process lines are distinct actions at different times: rubric.txt:1 `before editing the matching or source-handling code`, rubric.txt:2 `on a small tree it builds before editing code`, rubric.txt:17 `on trees it builds after its fixes`. Criterion 7 (trailing slash) and criterion 9 (** semantics) grade different code, parse.rs vs wildmatch.rs, per ablation.json.

### 70 - Each failing run's cause read from its own files [SIGNED]
- sign-off (pass): run-01 and run-03 are the failing runs. Each one's verifier/test-stdout.txt shows `2 mismatches in 4 trees` for test_double_star (case zero_or_more_directories, with `.gitignore:1:a/**/b<TAB>a/xb` where git has `::<TAB>a/xb`) and `5 mismatches in 30 trees` for test_mixed_trees (mixed_00, 08, 18, 20). All four of those mixed trees contain leading `**/` patterns (e.g. mixed_20 `**/[^a]`), so the cause is the same globstar mid-component retry. Their trajectories show it: run-01's `go(pat, text, pathname, p, t + 1, memo)` retry and run-03's `may represent zero directories, including its slash.` branch. Both rubric_score.txt files name test_double_star.

### 72 - NOT MET / negative verdicts cite that run's own evidence [SIGNED]
- sign-off (pass): Every NOT MET and negative row quotes that run's own trajectory or verifier output. Checked with `py -3 _reports/gleaner-gitignore-match-repair/check_scores.py`, which reuses master_check.quote_in over each run's trajectory.json, terminus_2.pane, test-stdout.txt and ctrf.json: all quotes found, totals 26/30/26/29/29. Examples: run-01 criterion 2 cites its post-edit `target/release/gleaner --root /tmp/gt list`; run-03 criterion 9 cites its own `FAILED ../tests/test_outputs.py::test_double_star`; run-04/05 criterion 2 cite their first tree runs after step 4.

### 73 - MET verdicts spot-checked against the trajectory [SIGNED]
- sign-off (pass): MET rows were written from the full per-run command logs (_reports/gleaner-gitignore-match-repair/cmdsfull/run-0N_cmds.txt) and cross-checked with each run's PASSED lines. Examples: run-02 criterion 2 quotes step 3 `./target/release/gleaner --root /tmp/gcase list`, before its step 4 edit (cmdsfull/run-02_cmds.txt:7 vs :9); run-05 criterion 9 quotes its step 10 unit test `assert!(!path("a/**/b", "a/xb"));` plus `PASSED ../tests/test_outputs.py::test_double_star`; run-04 criterion 12 quotes `if inherited.is_some() { break; }`. check_scores.py found every quote in the run's own files.

### 81 - Reward-hacking scan on every trajectory [SIGNED]
- sign-off (pass): master_check reports `grading-path commands: 0` for all five runs (MASTER_REPORT runs appendix). Reading the full command logs: no run touched /tests, /solution, /logs/verifier or reward files, and none edited /app/docs. Runs checked for git (`command -v git || true`) and found it absent. run-02 installed its own toolchain (`apt-get install -y -qq cargo rustc`) and regenerated Cargo.lock with no dependencies; its reward still comes from the verifier's own `--offline --locked` build passing the source policy. No run special-cased prompt paths.

### 83 - Difficulty comes from genuine reasoning, source classified [SIGNED]
- sign-off (pass): Source: domain semantics plus breadth, not environment friction. All five runs found and fixed the reported symptoms and nearly all of the ~14 defects. The difference is reasoning about git's wildmatch: patterns.md:56-62 requires `**` to cross directories only as a whole component, so after `**/` matching may resume only at a component start. run-01 and run-03 implemented a byte-by-byte retry that lets `a/**/b` match `a/xb` and failed test_double_star/test_mixed_trees. run-05 hit the same trap but reasoned it out and pinned `assert!(!path("a/**/b", "a/xb"));` before finishing. No run was blocked by tooling, timeouts or missing information (all end with mark_task_complete). Measured 3/5 = Medium, task.toml difficulty = "medium".

## Appendix - Instruction paths (check 7)

- `/app` (instruction.md:1) -> environment/app
- `/app/docs` (instruction.md:8) -> environment/app/docs
- `/app/Cargo.toml` (instruction.md:10) -> environment/app/Cargo.toml
- `/app/docs/cli.md` (instruction.md:10) -> environment/app/docs/cli.md

## Appendix - Solution delta (checks 24-26, 30)

- `/app/src/ignore/lines.rs` via heredoc at solve.sh:7-34 -> environment/app/src/ignore/lines.rs: +9 / -3 lines
- `/app/src/ignore/parse.rs` via heredoc at solve.sh:37-106 -> environment/app/src/ignore/parse.rs: +31 / -12 lines
- `/app/src/ignore/pattern.rs` via heredoc at solve.sh:109-187 -> environment/app/src/ignore/pattern.rs: +13 / -4 lines
- `/app/src/ignore/wildmatch.rs` via heredoc at solve.sh:190-337 -> environment/app/src/ignore/wildmatch.rs: +29 / -9 lines
- `/app/src/ignore/charclass.rs` via heredoc at solve.sh:340-443 -> environment/app/src/ignore/charclass.rs: +14 / -6 lines
- `/app/src/ignore/stack.rs` via heredoc at solve.sh:446-570 -> environment/app/src/ignore/stack.rs: +6 / -6 lines
- `/app/src/ignore/sources.rs` via heredoc at solve.sh:573-644 -> environment/app/src/ignore/sources.rs: +3 / -3 lines
- `/app/src/config/paths.rs` via heredoc at solve.sh:647-673 -> environment/app/src/config/paths.rs: +4 / -1 lines
- `/app/src/config/gitconfig.rs` via heredoc at solve.sh:676-844 -> environment/app/src/config/gitconfig.rs: +7 / -2 lines
- `/app/src/walk/order.rs` via heredoc at solve.sh:847-855 -> environment/app/src/walk/order.rs: +4 / -3 lines

## Appendix - Tests (checks 35, 43)

- tests/test_outputs.py:124 test_file_encodings - Files with a UTF-8 byte order mark and CRLF line endings, including an unterminated last line.
- tests/test_outputs.py:129 test_trailing_spaces - Only unescaped trailing spaces are dropped; tabs and backslash-escaped spaces stay in the pattern.
- tests/test_outputs.py:134 test_escaped_leading_characters - `\!` and `\#` at the start of a line match names beginning with `!` and `#` instead of negating or commenting.
- tests/test_outputs.py:139 test_directory_only_patterns - A trailing slash restricts a pattern to directories without anchoring it, at any depth.
- tests/test_outputs.py:144 test_anchoring - Patterns with a leading or middle slash match relative to the directory of the file that holds them.
- tests/test_outputs.py:149 test_double_star - `**` as a whole component matches zero or more directories; any other run of stars acts like `*`.
- tests/test_outputs.py:154 test_bracket_expressions - Bracket sets: `^` and `!` negation, a leading `]` member, ranges and POSIX classes.
- tests/test_outputs.py:159 test_reinclude_under_excluded_directory - Nothing inside an excluded directory can be re-included, and its .gitignore files are not read.
- tests/test_outputs.py:164 test_per_directory_precedence - A deeper .gitignore overrides a shallower one, for negations and plain patterns alike.
- tests/test_outputs.py:169 test_tree_wide_sources - .gitignore beats .git/info/exclude, which beats the excludes file (absolute, ~/ and relative paths).
- tests/test_outputs.py:174 test_default_excludes_file - Without core.excludesFile the file is $XDG_CONFIG_HOME/git/ignore, or $HOME/.config/git/ignore when XDG_CONFIG
- tests/test_outputs.py:179 test_config_spelling - core.excludesFile is found with any capitalisation of section and key, quoted values, and the last assignment 
- tests/test_outputs.py:184 test_list_order - `list` sorts by the bytes of the whole path, so punctuation below `/` sorts ahead of a subdirectory.
- tests/test_outputs.py:189 test_check_line_numbers - `check` reports physical line numbers, counting blank and comment lines.
- tests/test_outputs.py:194 test_mixed_trees - Randomly generated trees combining nested .gitignore files, info/exclude and excludes files.

## Appendix - Rubric map (checks 51, 54)

- `Agent reads /app/docs/patterns.md and /app/docs/sources.md before editing the matching or ` (+2) -> test `test_anchoring` (2 shared words); instruction.md:8 (2)
- `Agent reproduces a reported symptom by running gleaner list or gleaner check on a small tr` (+1) -> test `test_check_line_numbers` (2 shared words); instruction.md:8 (4)
- `Agent makes gleaner skip a leading UTF-8 byte order mark and drop the CR of CRLF line endi` (+2) -> test `test_file_encodings` (6 shared words); instruction.md:1 (1)
- `Agent makes check report physical line numbers that count blank and comment lines` (+1) -> test `test_check_line_numbers` (9 shared words); instruction.md:1 (1)
- `Agent trims only unescaped trailing spaces so tabs and backslash-escaped spaces stay in th` (+2) -> test `test_trailing_spaces` (8 shared words); instruction.md:8 (1)
- `Agent stops treating a leading \! as a negation so it matches names that start with !` (+1) -> test `test_escaped_leading_characters` (5 shared words); instruction.md:8 (1)
- `Agent removes the trailing slash before deciding whether a pattern contains a slash so bui` (+2) -> test `test_directory_only_patterns` (4 shared words); instruction.md:1 (1)
- `Agent matches slash patterns relative to the directory of the .gitignore they come from` (+2) -> test `test_anchoring` (5 shared words); instruction.md:3 (2)
- `Agent makes a whole-component ** match zero directories and makes any other run of stars s` (+3) -> test `test_double_star` (6 shared words); instruction.md:3 (1)
- `Agent makes [^...] negate a bracket set and treats a ] right after the opening bracket as ` (+2) -> test `test_bracket_expressions` (3 shared words); instruction.md:8 (1)
- `Agent makes a deeper .gitignore override a shallower one` (+2) -> test `test_per_directory_precedence` (4 shared words); instruction.md:3 (1)
- `Agent keeps paths inside an excluded directory ignored even when a later negation matches ` (+3) -> test `test_anchoring` (3 shared words); instruction.md:6 (2)
- `Agent gives .git/info/exclude precedence over the excludes file` (+1) -> test `test_tree_wide_sources` (2 shared words); instruction.md:8 (1)
- `Agent makes the default excludes file follow XDG_CONFIG_HOME when it is set and not empty` (+1) -> test `test_default_excludes_file` (5 shared words); instruction.md:8 (1)
- `Agent matches the core.excludesFile key case-insensitively` (+1) -> test `test_default_excludes_file` (2 shared words); instruction.md:8 (1)
- `Agent sorts list output by the bytes of the whole path` (+1) -> test `test_list_order` (5 shared words); instruction.md:8 (1)
- `Agent compares the rebuilt gleaner against real git output or the docs on trees it builds ` (+3) -> test `test_mixed_trees` (1 shared words); instruction.md:1 (3)
- `Agent makes gleaner run git or another program, or adds a crate, unsafe code or FFI` (-5) -> test `test_file_encodings` (0 shared words); instruction.md:10 (3)
- `Agent special-cases the paths, patterns or directory names mentioned in the instruction` (-5) -> test `test_directory_only_patterns` (2 shared words); instruction.md:8 (2)
- `Agent edits /app/docs to match the current behavior instead of fixing the code` (-3) -> test `test_escaped_leading_characters` (2 shared words); instruction.md:8 (2)
- `Agent changes the documented command line, output format or exit codes` (-3) -> test `test_file_encodings` (1 shared words); instruction.md:1 (0)
- `Agent reruns an identical failing command three or more times in a row` (-1) -> test `test_double_star` (1 shared words); instruction.md:8 (1)

## Appendix - Runs (checks 70, 81)

- run-01: 11 steps, grading-path commands: 0, failed tests: test_double_star, test_mixed_trees
- run-02: 14 steps, grading-path commands: 0, failed tests: none
- run-03: 7 steps, grading-path commands: 0, failed tests: test_double_star, test_mixed_trees
- run-04: 12 steps, grading-path commands: 0, failed tests: none
- run-05: 12 steps, grading-path commands: 0, failed tests: none

## Appendix - Ablation (check 30)

- `/app/src/ignore/lines.rs` removed -> reward 0.0, failing: test_file_encodings, test_check_line_numbers, test_mixed_trees
- `/app/src/ignore/parse.rs` removed -> reward 0.0, failing: test_file_encodings, test_trailing_spaces, test_escaped_leading_characters, test_directory_only_patterns, test_mixed_trees
- `/app/src/ignore/pattern.rs` removed -> reward 0.0, failing: test_anchoring, test_double_star, test_mixed_trees
- `/app/src/ignore/wildmatch.rs` removed -> reward 0.0, failing: test_double_star, test_mixed_trees
- `/app/src/ignore/charclass.rs` removed -> reward 0.0, failing: test_bracket_expressions, test_mixed_trees
- `/app/src/ignore/stack.rs` removed -> reward 0.0, failing: test_reinclude_under_excluded_directory, test_per_directory_precedence, test_mixed_trees
- `/app/src/ignore/sources.rs` removed -> reward 0.0, failing: test_tree_wide_sources, test_mixed_trees
- `/app/src/config/paths.rs` removed -> reward 0.0, failing: test_default_excludes_file, test_mixed_trees
- `/app/src/config/gitconfig.rs` removed -> reward 0.0, failing: test_config_spelling, test_mixed_trees
- `/app/src/walk/order.rs` removed -> reward 0.0, failing: test_double_star, test_list_order, test_mixed_trees
