# Master Ship Checklist - sshcfg-resolve-repair

Bundle sha `b4ba95ec1d04b850`, generated 2026-09-27 02:35. FAIL 2, STALE 0, REVIEW 4, MANUAL 39, SIGNED 0, PASS 42

| # | Sec | Check | Mode | Status | First finding |
|---|---|---|---|---|---|
| CI | - | CI / pool static gates (pinned deps, base image, test.sh, docstrings, ruff, diversity) | auto | **REVIEW** | [toml] difficulty is 'unknown' — set it from the run_k.sh k=5 result before submitting |
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
| 31 | C | Cold linux/amd64 oracle build runs cleanly | auto | **PASS** | cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-27T02:31:02 (baselines.json) |
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
| 43 | D | Test names describe what they check | assist | **REVIEW** | tests/test_outputs.py:143 test_precedence_and_lists: name words ['precedence', 'lists'] do not appear in its docstring/b |
| 44 | D | Fail-closed tests carry a positive control | assist | **MANUAL** |  |
| 45 | D | Evidence test counts match current tests/ | auto | **PASS** |  |
| 46 | E | schema_version = "1.1" is the first line | auto | **PASS** |  |
| 47 | E | description/keywords/authors/category/tags accurate | assist | **MANUAL** |  |
| 48 | E | All timeouts are 7200 | auto | **PASS** |  |
| 49 | E | No reference_pattern / pipeline metadata | auto | **PASS** |  |
| 50 | E | allow_internet = true and no offline instruction | auto | **PASS** |  |
| 51 | F | Every rubric line maps to a test or instruction | assist | **REVIEW** | rubric line "Agent reads /app/docs/cli.md before editing files under /app/src" maps to no test and no instruction senten |
| 52 | F | Rubric format 'Agent ..., +/-N', no headers/blank lines | auto | **PASS** |  |
| 53 | F | No mutually contradictory rubric lines | manual | **MANUAL** |  |
| 54 | F | No double-counted behavior | assist | **MANUAL** |  |
| 55 | F | rubric_score arithmetic consistent with rubric.txt | auto | **PASS** |  |
| 56 | F | Rubric cites only mechanisms that exist | auto | **REVIEW** | rubric line cites `/app/t/cases`, which exists nowhere in the image, instruction or tests |
| 57 | H | Evidence structure exact | auto | **PASS** |  |
| 58 | H | Oracle x3 full credit, every test passing | auto | **PASS** |  |
| 59 | H | NOP x2 zero credit, every test 'failed' | auto | **PASS** |  |
| 60 | H | NOP failures are genuine assertion mismatches | auto | **PASS** |  |
| 61 | H | Evidence newer than every graded file | auto | **PASS** |  |
| 62 | H | Evidence not duplicated | auto | **PASS** |  |
| 63 | G | SUMMARY.txt exactly 2 lines | auto | **FAIL** | [63] trajectories/SUMMARY.txt missing |
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
| 77 | G | agent/ file sets identical across runs | auto | **FAIL** | [77] missing trajectories/run-01/ |
| 78 | G | verifier/ files present, reward matches ctrf | auto | **PASS** |  |
| 79 | G | reasoning_effort xhigh on every run | auto | **PASS** |  |
| 80 | G | No exception_info in any result.json | auto | **PASS** |  |
| 81 | G | Reward-hacking scan on every trajectory | assist | **MANUAL** |  |
| 82 | G | Evidence regenerated atomically after the last k=5 | auto | **PASS** |  |
| 83 | I | Difficulty comes from genuine reasoning, source classified | manual | **MANUAL** |  |
| 84 | I | Delivery structure exact, no junk | auto | **PASS** |  |
| 85 | I | Final stb / personal-path scrub across the whole bundle | auto | **PASS** |  |

## Findings and sign-offs

### CI - CI / pool static gates (pinned deps, base image, test.sh, docstrings, ruff, diversity) [REVIEW]
- warn: [toml] difficulty is 'unknown' — set it from the run_k.sh k=5 result before submitting

### 31 - Cold linux/amd64 oracle build runs cleanly [PASS]
- info: cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-27T02:31:02 (baselines.json)

### 43 - Test names describe what they check [REVIEW]
- warn: tests/test_outputs.py:143 test_precedence_and_lists: name words ['precedence', 'lists'] do not appear in its docstring/body - confirm the name describes the check

### 51 - Every rubric line maps to a test or instruction [REVIEW]
- warn: rubric line "Agent reads /app/docs/cli.md before editing files under /app/src" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent writes its own ssh_config fixtures and runs hopcfg on them to reproduce a mismatch before chan" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent keeps an earlier ProxyCommand from being replaced by a later ProxyJump" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent applies the 300 second ServerAliveInterval default when BatchMode is yes" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent prints SILENT for the quiet log level" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent makes %k fall back to the destination as typed when no HostKeyAlias is set" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent rebuilds with make and runs make check after the last source edit" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent edits expected files under /app/t/cases to make make check pass" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent reruns an identical failing command three or more times in a row" maps to no test and no instruction sentence - confirm what grades it

### 56 - Rubric cites only mechanisms that exist [REVIEW]
- warn: rubric line cites `/app/t/cases`, which exists nowhere in the image, instruction or tests

### 63 - SUMMARY.txt exactly 2 lines [FAIL]
- error: [63] trajectories/SUMMARY.txt missing

### 77 - agent/ file sets identical across runs [FAIL]
- error: [77] missing trajectories/run-01/
- error: [77] missing trajectories/run-02/
- error: [77] missing trajectories/run-03/
- error: [77] missing trajectories/run-04/
- error: [77] missing trajectories/run-05/

## Appendix - Instruction paths (check 7)

- `/app` (instruction.md:1) -> environment/app
- `/app/docs/cli.md` (instruction.md:3) -> environment/app/docs/cli.md
- `/app/src` (instruction.md:5) -> environment/app/src

## Appendix - Stated constants (checks 6, 40)

- instruction.md:3 `255` -> present in tests/

## Appendix - Solution delta (checks 24-26, 30)

- `/app/src/readconf.c` via patch at solve.sh:6-81 -> environment/app/src/readconf.c
- `/app/src/matchcfg.c` via patch at solve.sh:83-103 -> environment/app/src/matchcfg.c
- `/app/src/main.c` via patch at solve.sh:105-127 -> environment/app/src/main.c
- `/app/src/convtime.c` via patch at solve.sh:129-141 -> environment/app/src/convtime.c
- `/app/src/strlist.c` via patch at solve.sh:143-155 -> environment/app/src/strlist.c
- `/app/src/jump.c` via patch at solve.sh:157-169 -> environment/app/src/jump.c
- `/app/src/options.c` via patch at solve.sh:171-183 -> environment/app/src/options.c
- `/app/src/dump.c` via patch at solve.sh:185-197 -> environment/app/src/dump.c

## Appendix - Tests (checks 35, 43)

- tests/test_outputs.py:118 test_host_line_patterns - Host lines: wildcards, case-sensitive raw-name matching, negated patterns anywhere on the line.
- tests/test_outputs.py:123 test_match_criteria - Match host/originalhost/user/localuser/canonical/all criteria, incl. HostName-based host matching.
- tests/test_outputs.py:128 test_final_pass - Match final triggers a second pass that matches Host/Match against the resolved host name.
- tests/test_outputs.py:133 test_include_scoping - Include inside Host/Match blocks, globbed file order and the active state around each included file.
- tests/test_outputs.py:138 test_include_paths - Relative, absolute and ~ Include paths resolve to the same files ssh reads.
- tests/test_outputs.py:143 test_precedence_and_lists - First obtained value wins across -o/-l/-p/destination/config; list keywords accumulate and dedupe like ssh.
- tests/test_outputs.py:148 test_sendenv_setenv - SendEnv accumulation and -pattern removal, SetEnv first-line-wins semantics.
- tests/test_outputs.py:153 test_time_values - Time values with compound units, none, ControlPersist forms and keep-alive defaults and aliases.
- tests/test_outputs.py:158 test_proxy_settings - ProxyJump/ProxyCommand interplay, jump host formatting and jump host loop rejection.
- tests/test_outputs.py:163 test_token_expansion - HostName %h expansion and normalisation plus %-token, ${ENV} and ~ expansion in path keywords.
- tests/test_outputs.py:168 test_syntax_and_rejections - Keyword/value spelling variants print like ssh, and invalid configs or destinations exit 255 with no output.

## Appendix - Rubric map (checks 51, 54)

- `Agent reads /app/docs/cli.md before editing files under /app/src` (+1) -> test `test_include_paths` (1 shared words); instruction.md:1 (0)
- `Agent compares hopcfg output with real ssh -G output for the same config files and argumen` (+2) -> test `test_syntax_and_rejections` (2 shared words); instruction.md:1 (2)
- `Agent writes its own ssh_config fixtures and runs hopcfg on them to reproduce a mismatch b` (+2) -> test `test_precedence_and_lists` (1 shared words); instruction.md:1 (1)
- `Agent makes a matching negated pattern on a Host line disable the whole line wherever it a` (+3) -> test `test_host_line_patterns` (5 shared words); instruction.md:3 (3)
- `Agent makes Match host evaluate against the %h-expanded HostName when one is set` (+3) -> test `test_match_criteria` (3 shared words); instruction.md:3 (4)
- `Agent makes the Match final pass match Host and Match lines against the resolved host name` (+3) -> test `test_final_pass` (7 shared words); instruction.md:1 (4)
- `Agent restores the enclosing active state after each file expanded from an Include glob` (+2) -> test `test_include_scoping` (3 shared words); instruction.md:3 (2)
- `Agent resolves relative Include paths against ~/.ssh instead of the including file's direc` (+2) -> test `test_include_paths` (4 shared words); instruction.md:3 (2)
- `Agent makes compound time values such as 1h30m add up all their parts` (+2) -> test `test_time_values` (3 shared words); instruction.md:3 (2)
- `Agent makes SendEnv -pattern entries remove every earlier variable the pattern matches` (+2) -> test `test_sendenv_setenv` (3 shared words); instruction.md:1 (1)
- `Agent makes only the first SetEnv line that applies take effect` (+2) -> test `test_sendenv_setenv` (3 shared words); instruction.md:3 (1)
- `Agent keeps an earlier ProxyCommand from being replaced by a later ProxyJump` (+2) -> test `test_proxy_settings` (1 shared words); instruction.md:1 (1)
- `Agent applies the 300 second ServerAliveInterval default when BatchMode is yes` (+2) -> test `test_final_pass` (1 shared words); instruction.md:1 (0)
- `Agent prints SILENT for the quiet log level` (+1) -> test `test_syntax_and_rejections` (1 shared words); instruction.md:1 (0)
- `Agent makes %k fall back to the destination as typed when no HostKeyAlias is set` (+2) -> test `test_precedence_and_lists` (1 shared words); instruction.md:1 (0)
- `Agent rebuilds with make and runs make check after the last source edit` (+1) -> test `test_host_line_patterns` (0 shared words); instruction.md:3 (1)
- `Agent makes hopcfg invoke ssh or any other program through exec, system or popen` (-5) -> test `test_host_line_patterns` (0 shared words); instruction.md:5 (5)
- `Agent hardcodes output for specific host names or config contents` (-5) -> test `test_syntax_and_rejections` (2 shared words); instruction.md:1 (2)
- `Agent edits /app/docs/cli.md to redefine the output keywords or known differences instead ` (-3) -> test `test_syntax_and_rejections` (2 shared words); instruction.md:3 (2)
- `Agent edits expected files under /app/t/cases to make make check pass` (-2) -> test `test_final_pass` (1 shared words); instruction.md:3 (1)
- `Agent reruns an identical failing command three or more times in a row` (-1) -> test `test_host_line_patterns` (0 shared words); instruction.md:1 (1)

## Appendix - Ablation (check 30)

- `/app/src/readconf.c` removed -> reward 0.0, failing: test_host_line_patterns, test_include_scoping, test_include_paths, test_sendenv_setenv
- `/app/src/matchcfg.c` removed -> reward 0.0, failing: test_match_criteria
- `/app/src/main.c` removed -> reward 0.0, failing: test_final_pass, test_token_expansion
- `/app/src/convtime.c` removed -> reward 0.0, failing: test_time_values
- `/app/src/strlist.c` removed -> reward 0.0, failing: test_final_pass, test_sendenv_setenv
- `/app/src/jump.c` removed -> reward 0.0, failing: test_proxy_settings
- `/app/src/options.c` removed -> reward 0.0, failing: test_time_values
- `/app/src/dump.c` removed -> reward 0.0, failing: test_precedence_and_lists, test_syntax_and_rejections
