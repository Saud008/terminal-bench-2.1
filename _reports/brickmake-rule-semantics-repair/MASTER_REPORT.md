# Master Ship Checklist - brickmake-rule-semantics-repair

Bundle sha `0babf476219b8958`, generated 2026-09-26 21:01. FAIL 0, STALE 0, REVIEW 1, MANUAL 41, SIGNED 0, PASS 45

| # | Sec | Check | Mode | Status | First finding |
|---|---|---|---|---|---|
| CI | - | CI / pool static gates (pinned deps, base image, test.sh, docstrings, ruff, diversity) | auto | **PASS** |  |
| 0 | A | Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens | assist | **MANUAL** |  |
| 1 | A | Every stated requirement is exercised by a test | assist | **MANUAL** |  |
| 2 | A | Every requirement a test enforces is stated | assist | **MANUAL** |  |
| 3 | A | No implementation-step ('how') sentences | assist | **MANUAL** |  |
| 4 | A | Interface contracts named in the prompt are really graded | manual | **MANUAL** |  |
| 5 | A | No grader / test-suite / pipeline terms | auto | **PASS** |  |
| 6 | A | Stated constants match tests byte for byte | assist | **MANUAL** |  |
| 7 | A | Every path the prompt names exists in the built image | auto | **PASS** |  |
| 8 | A | Output schema exactness in prose matches the tests | assist | **MANUAL** |  |
| 9 | A | No self-contradiction between sentences | manual | **MANUAL** |  |
| 10 | A | Prompt does not narrate each planted defect's mechanism | assist | **MANUAL** |  |
| 11 | B | Every environment file is required | manual | **MANUAL** |  |
| 12 | B | No BUG/FIXME/planted/intent comments (grep) | auto | **PASS** |  |
| 13 | B | No comments echoing instruction or rubric text | assist | **MANUAL** |  |
| 14 | B | No lore/notes doc indexing the planted defects | assist | **MANUAL** |  |
| 15 | B | No opaque short file/module names | auto | **PASS** |  |
| 16 | B | No names that mislabel behavior | manual | **MANUAL** |  |
| 17 | B | No dead / orphaned files | auto | **PASS** |  |
| 18 | B | No unused module that already implements the answer | manual | **MANUAL** |  |
| 19 | B | Authoritative docs consistent with instruction.md | manual | **MANUAL** |  |
| 20 | B | Non-authoritative docs hold no hidden graded rule | manual | **MANUAL** |  |
| 21 | B | Vendored archives/binaries carry no host metadata | auto | **PASS** |  |
| 22 | B | Dockerfile never copies solution/ or tests/ | auto | **PASS** |  |
| 23 | B | Decoys are reachable, fair and not labelled | assist | **MANUAL** |  |
| 24 | C | solve.sh delta listed file by file | assist | **MANUAL** |  |
| 25 | C | Every touched file maps to a requested fix (no no-op delta) | assist | **MANUAL** |  |
| 26 | C | No out-of-scope delta | manual | **MANUAL** |  |
| 27 | C | Reference output independently re-derived | manual | **MANUAL** |  |
| 28 | C | Agent consensus vs reference outlier checked | manual | **MANUAL** |  |
| 29 | C | No orphaned files in solution/ | auto | **PASS** |  |
| 30 | C | Each fix ablated alone produces test failures | auto | **PASS** |  |
| 31 | C | Cold linux/amd64 oracle build runs cleanly | auto | **MANUAL** | no baselines.json - run `py -3 tb21/run_baselines.py <slug>` to automate this check |
| 32 | D | Zero individual tests pass under NOP | auto | **PASS** |  |
| 33 | D | Guard-style tests are coupled to real behavior | assist | **MANUAL** |  |
| 34 | D | NOP-passable guards coupled, not deleted | manual | **MANUAL** |  |
| 35 | D | Assertions do what names/docstrings claim | assist | **MANUAL** |  |
| 36 | D | Expected values never computed by agent-editable code | assist | **MANUAL** |  |
| 37 | D | Fixtures feeding expected values are not agent-editable | assist | **MANUAL** |  |
| 38 | D | Held-out scenarios really change the graded outcome | manual | **MANUAL** |  |
| 39 | D | Exactness rules enforced literally (set equality) | assist | **MANUAL** |  |
| 40 | D | Test tolerances equal the stated tolerances | assist | **MANUAL** |  |
| 41 | D | No string obfuscation in tests | auto | **PASS** |  |
| 42 | D | No dead test helpers | auto | **PASS** |  |
| 43 | D | Test names describe what they check | assist | **MANUAL** |  |
| 44 | D | Fail-closed tests carry a positive control | assist | **MANUAL** |  |
| 45 | D | Evidence test counts match current tests/ | auto | **PASS** |  |
| 46 | E | schema_version = "1.1" is the first line | auto | **PASS** |  |
| 47 | E | description/keywords/authors/category/tags accurate | assist | **MANUAL** |  |
| 48 | E | All timeouts are 7200 | auto | **PASS** |  |
| 49 | E | No reference_pattern / pipeline metadata | auto | **PASS** |  |
| 50 | E | allow_internet = true and no offline instruction | auto | **PASS** |  |
| 51 | F | Every rubric line maps to a test or instruction | assist | **REVIEW** | rubric line "Agent reproduces at least one reported symptom with a scratch makefile before editing" maps to no test and  |
| 52 | F | Rubric format 'Agent ..., +/-N', no headers/blank lines | auto | **PASS** |  |
| 53 | F | No mutually contradictory rubric lines | manual | **MANUAL** |  |
| 54 | F | No double-counted behavior | assist | **MANUAL** |  |
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
| 70 | G | Each failing run's cause read from its own files | assist | **MANUAL** |  |
| 71 | G | rubric_score files not copies of each other | auto | **PASS** |  |
| 72 | G | NOT MET / negative verdicts cite that run's own evidence | assist | **MANUAL** |  |
| 73 | G | MET verdicts spot-checked against the trajectory | assist | **MANUAL** |  |
| 74 | G | PII scrub clean across trajectory files | auto | **PASS** |  |
| 75 | G | config.json paths scrubbed to /terminal-bench2.1/<slug> | auto | **PASS** |  |
| 76 | G | result.json model names left raw | auto | **PASS** |  |
| 77 | G | agent/ file sets identical across runs | auto | **PASS** |  |
| 78 | G | verifier/ files present, reward matches ctrf | auto | **PASS** |  |
| 79 | G | reasoning_effort xhigh on every run | auto | **PASS** |  |
| 80 | G | No exception_info in any result.json | auto | **PASS** |  |
| 81 | G | Reward-hacking scan on every trajectory | assist | **MANUAL** | [81] run-02: trajectory mentions grading paths ['/tests/'] — read and confirm no reads/writes (no agent command touched  |
| 82 | G | Evidence regenerated atomically after the last k=5 | auto | **PASS** |  |
| 83 | I | Difficulty comes from genuine reasoning, source classified | manual | **MANUAL** |  |
| 84 | I | Delivery structure exact, no junk | auto | **PASS** |  |
| 85 | I | Final stb / personal-path scrub across the whole bundle | auto | **PASS** |  |

## Findings and sign-offs

### 0 - Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens [MANUAL]

### 1 - Every stated requirement is exercised by a test [MANUAL]

### 2 - Every requirement a test enforces is stated [MANUAL]

### 3 - No implementation-step ('how') sentences [MANUAL]

### 4 - Interface contracts named in the prompt are really graded [MANUAL]

### 6 - Stated constants match tests byte for byte [MANUAL]

### 8 - Output schema exactness in prose matches the tests [MANUAL]

### 9 - No self-contradiction between sentences [MANUAL]

### 10 - Prompt does not narrate each planted defect's mechanism [MANUAL]

### 11 - Every environment file is required [MANUAL]

### 13 - No comments echoing instruction or rubric text [MANUAL]

### 14 - No lore/notes doc indexing the planted defects [MANUAL]

### 16 - No names that mislabel behavior [MANUAL]

### 18 - No unused module that already implements the answer [MANUAL]

### 19 - Authoritative docs consistent with instruction.md [MANUAL]

### 20 - Non-authoritative docs hold no hidden graded rule [MANUAL]

### 23 - Decoys are reachable, fair and not labelled [MANUAL]

### 24 - solve.sh delta listed file by file [MANUAL]

### 25 - Every touched file maps to a requested fix (no no-op delta) [MANUAL]

### 26 - No out-of-scope delta [MANUAL]

### 27 - Reference output independently re-derived [MANUAL]

### 28 - Agent consensus vs reference outlier checked [MANUAL]

### 30 - Each fix ablated alone produces test failures [PASS]

### 31 - Cold linux/amd64 oracle build runs cleanly [MANUAL]
- info: no baselines.json - run `py -3 tb21/run_baselines.py <slug>` to automate this check

### 33 - Guard-style tests are coupled to real behavior [MANUAL]

### 34 - NOP-passable guards coupled, not deleted [MANUAL]

### 35 - Assertions do what names/docstrings claim [MANUAL]

### 36 - Expected values never computed by agent-editable code [MANUAL]

### 37 - Fixtures feeding expected values are not agent-editable [MANUAL]

### 38 - Held-out scenarios really change the graded outcome [MANUAL]

### 39 - Exactness rules enforced literally (set equality) [MANUAL]

### 40 - Test tolerances equal the stated tolerances [MANUAL]

### 43 - Test names describe what they check [MANUAL]

### 44 - Fail-closed tests carry a positive control [MANUAL]

### 47 - description/keywords/authors/category/tags accurate [MANUAL]

### 51 - Every rubric line maps to a test or instruction [REVIEW]
- warn: rubric line "Agent reproduces at least one reported symptom with a scratch makefile before editing" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent special-cases the file names or flags quoted in the instruction or docs examples" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent reruns an identical failing command three or more times in a row" maps to no test and no instruction sentence - confirm what grades it

### 53 - No mutually contradictory rubric lines [MANUAL]

### 54 - No double-counted behavior [MANUAL]

### 70 - Each failing run's cause read from its own files [MANUAL]

### 72 - NOT MET / negative verdicts cite that run's own evidence [MANUAL]

### 73 - MET verdicts spot-checked against the trajectory [MANUAL]

### 81 - Reward-hacking scan on every trajectory [MANUAL]
- info: [81] run-02: trajectory mentions grading paths ['/tests/'] — read and confirm no reads/writes (no agent command touched them - mention is in output/prose only)

### 83 - Difficulty comes from genuine reasoning, source classified [MANUAL]

## Appendix - Instruction paths (check 7)

- `/app` (instruction.md:1) -> environment/app
- `/app/docs` (instruction.md:9) -> environment/app/docs
- `/app/cmd/brickmake` (instruction.md:11) -> environment/app/cmd/brickmake
- `/app/docs/cli.md` (instruction.md:11) -> environment/app/docs/cli.md

## Appendix - Stated constants (checks 6, 40)

- instruction.md:9 `4.3` -> present in tests/

## Appendix - Solution delta (checks 24-26, 30)

- `/app/internal/engine/implicit.go` via heredoc at solve.sh:6-216 -> environment/app/internal/engine/implicit.go: +11 / -6 lines
- `/app/internal/engine/scope.go` via heredoc at solve.sh:218-271 -> environment/app/internal/engine/scope.go: +11 / -6 lines
- `/app/internal/engine/update.go` via heredoc at solve.sh:273-458 -> environment/app/internal/engine/update.go: +5 / -5 lines
- `/app/internal/engine/engine.go` via heredoc at solve.sh:460-569 -> environment/app/internal/engine/engine.go: +2 / -1 lines
- `/app/internal/engine/deps.go` via heredoc at solve.sh:571-668 -> environment/app/internal/engine/deps.go: +11 / -4 lines
- `/app/internal/expand/define.go` via heredoc at solve.sh:670-757 -> environment/app/internal/expand/define.go: +15 / -2 lines

## Appendix - Tests (checks 35, 43)

- tests/test_outputs.py:50 test_shortest_stem_selection - Among matching pattern rules the one with the shortest stem wins, where the
- tests/test_outputs.py:56 test_directory_relative_prerequisites - For a slash-less target pattern matched against a name with a directory, the
- tests/test_outputs.py:62 test_mentioned_prerequisite_ought_to_exist - A prerequisite that is mentioned anywhere in the makefile counts as one that
- tests/test_outputs.py:68 test_timestamps_reread_after_recipe - After a recipe runs the target's time is read again, so a recipe that leaves its
- tests/test_outputs.py:74 test_per_goal_messages - 'Nothing to be done' and 'is up to date' are reported per goal, based only on
- tests/test_outputs.py:80 test_pattern_specific_variable_order - Pattern-specific variables from all matching patterns apply from the shortest
- tests/test_outputs.py:86 test_target_variable_inheritance - A target's own pattern-specific variables take precedence over the variables it
- tests/test_outputs.py:92 test_append_semantics - '+=' on a simply expanded variable expands the added text immediately and keeps
- tests/test_outputs.py:98 test_prerequisite_merge_order - A target's prerequisites from several rules are combined with the rule that has
- tests/test_outputs.py:104 test_project_builds - Multi-step incremental builds of small projects produce the same commands,

## Appendix - Rubric map (checks 51, 54)

- `Agent reads the relevant sections of /app/docs (rules.md, variables.md, updating.md) befor` (+2) -> test `test_append_semantics` (2 shared words); instruction.md:4 (1)
- `Agent reproduces at least one reported symptom with a scratch makefile before editing` (+2) -> test `test_shortest_stem_selection` (1 shared words); instruction.md:9 (1)
- `Agent fixes pattern-rule selection so the stem length includes the directory part of a dir` (+3) -> test `test_shortest_stem_selection` (7 shared words); instruction.md:6 (2)
- `Agent limits the directory prefix of a directory-relative match to prerequisites that cont` (+2) -> test `test_directory_relative_prerequisites` (5 shared words); instruction.md:6 (2)
- `Agent treats a prerequisite that is mentioned anywhere in the makefile as one that ought t` (+2) -> test `test_mentioned_prerequisite_ought_to_exist` (10 shared words); instruction.md:6 (3)
- `Agent orders pattern-specific variables by pattern length and places the file's own patter` (+3) -> test `test_pattern_specific_variable_order` (5 shared words); instruction.md:1 (0)
- `Agent makes '+=' on a simply expanded variable expand the added text at once and keeps a t` (+3) -> test `test_append_semantics` (8 shared words); instruction.md:1 (1)
- `Agent re-reads a target's time after its recipe runs instead of marking it as newest` (+2) -> test `test_timestamps_reread_after_recipe` (5 shared words); instruction.md:4 (1)
- `Agent reports "up to date" / "Nothing to be done" per goal based only on commands run for ` (+2) -> test `test_per_goal_messages` (7 shared words); instruction.md:5 (5)
- `Agent combines a target's prerequisites from several rules with the recipe rule's list fir` (+2) -> test `test_prerequisite_merge_order` (10 shared words); instruction.md:6 (2)
- `Agent rebuilds brickmake and compares its output against GNU make or the documented exampl` (+3) -> test `test_timestamps_reread_after_recipe` (3 shared words); instruction.md:1 (2)
- `Agent makes brickmake shell out to or embed GNU make instead of fixing its own logic` (-5) -> test `test_timestamps_reread_after_recipe` (1 shared words); instruction.md:1 (2)
- `Agent special-cases the file names or flags quoted in the instruction or docs examples` (-5) -> test `test_pattern_specific_variable_order` (1 shared words); instruction.md:3 (1)
- `Agent edits /app/docs to match the existing behavior instead of fixing the code` (-3) -> test `test_shortest_stem_selection` (1 shared words); instruction.md:9 (2)
- `Agent changes the command-line interface documented in /app/docs/cli.md` (-3) -> test `test_pattern_specific_variable_order` (2 shared words); instruction.md:5 (2)
- `Agent reruns an identical failing command three or more times in a row` (-1) -> test `test_timestamps_reread_after_recipe` (1 shared words); instruction.md:5 (1)

## Appendix - Runs (checks 70, 81)

- run-01: 31 steps, grading-path commands: 0, failed tests: test_mentioned_prerequisite_ought_to_exist
- run-02: 36 steps, grading-path commands: 0, failed tests: none
- run-03: 34 steps, grading-path commands: 0, failed tests: test_shortest_stem_selection, test_mentioned_prerequisite_ought_to_exist, test_append_semantics
- run-04: 47 steps, grading-path commands: 0, failed tests: test_append_semantics
- run-05: 40 steps, grading-path commands: 0, failed tests: test_append_semantics

## Appendix - Ablation (check 30)

- `/app/internal/engine/implicit.go` removed -> reward 0.0, failing: test_shortest_stem_selection, test_directory_relative_prerequisites, test_mentioned_prerequisite_ought_to_exist
- `/app/internal/engine/scope.go` removed -> reward 0.0, failing: test_pattern_specific_variable_order, test_target_variable_inheritance, test_project_builds
- `/app/internal/engine/update.go` removed -> reward 0.0, failing: test_timestamps_reread_after_recipe, test_project_builds
- `/app/internal/engine/engine.go` removed -> reward 0.0, failing: test_timestamps_reread_after_recipe, test_per_goal_messages, test_project_builds
- `/app/internal/engine/deps.go` removed -> reward 0.0, failing: test_prerequisite_merge_order
- `/app/internal/expand/define.go` removed -> reward 0.0, failing: test_pattern_specific_variable_order, test_append_semantics, test_project_builds
