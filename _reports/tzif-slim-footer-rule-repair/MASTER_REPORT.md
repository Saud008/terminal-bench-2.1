# Master Ship Checklist - tzif-slim-footer-rule-repair

Bundle sha `fa5ea17b4cc9cef5`, generated 2026-09-26 20:57. FAIL 2, STALE 0, REVIEW 4, MANUAL 41, SIGNED 0, PASS 40

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
| 15 | B | No opaque short file/module names | auto | **REVIEW** | [naming] environment/app/internal/posixtz/tz.go: opaque short name — must be decodable (ship check 15) |
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
| 30 | C | Each fix ablated alone produces test failures | auto | **MANUAL** | no ablation.json - run `py -3 tb21/run_baselines.py <slug> --ablate` to automate this check |
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
| 43 | D | Test names describe what they check | assist | **REVIEW** | tests/test_outputs.py:72 test_us_rules_after_table_end: name words ['rules', 'after'] do not appear in its docstring/bod |
| 44 | D | Fail-closed tests carry a positive control | assist | **MANUAL** |  |
| 45 | D | Evidence test counts match current tests/ | auto | **PASS** |  |
| 46 | E | schema_version = "1.1" is the first line | auto | **PASS** |  |
| 47 | E | description/keywords/authors/category/tags accurate | assist | **MANUAL** |  |
| 48 | E | All timeouts are 7200 | auto | **PASS** |  |
| 49 | E | No reference_pattern / pipeline metadata | auto | **PASS** |  |
| 50 | E | allow_internet = true and no offline instruction | auto | **PASS** |  |
| 51 | F | Every rubric line maps to a test or instruction | assist | **REVIEW** | rubric line "Agent reruns an identical failing command three or more times in a row" maps to no test and no instruction  |
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

### 15 - No opaque short file/module names [REVIEW]
- warn: [naming] environment/app/internal/posixtz/tz.go: opaque short name — must be decodable (ship check 15)
- warn: [naming] environment/app/cmd/shiftclock/at.go: opaque short name — must be decodable (ship check 15)

### 30 - Each fix ablated alone produces test failures [MANUAL]
- info: no ablation.json - run `py -3 tb21/run_baselines.py <slug> --ablate` to automate this check

### 31 - Cold linux/amd64 oracle build runs cleanly [MANUAL]
- info: no baselines.json - run `py -3 tb21/run_baselines.py <slug>` to automate this check

### 43 - Test names describe what they check [REVIEW]
- warn: tests/test_outputs.py:72 test_us_rules_after_table_end: name words ['rules', 'after'] do not appear in its docstring/body - confirm the name describes the check
- warn: tests/test_outputs.py:82 test_daylight_time_spanning_new_year: name words ['daylight', 'time', 'spanning', 'year'] do not appear in its docstring/body - confirm the name describes the check

### 51 - Every rubric line maps to a test or instruction [REVIEW]
- warn: rubric line "Agent reruns an identical failing command three or more times in a row" maps to no test and no instruction sentence - confirm what grades it

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
- `/app/zones` (instruction.md:1) -> environment/app/zones
- `/app/docs/cli.md` (instruction.md:3) -> environment/app/docs/cli.md
- `/app/cmd/shiftclock` (instruction.md:3) -> environment/app/cmd/shiftclock

## Appendix - Solution delta (checks 24-26, 30)

- `/app/internal/posixtz/hms.go` via heredoc at solve.sh:8-66 -> environment/app/internal/posixtz/hms.go: +3 / -6 lines
- `/app/internal/posixtz/rule.go` via heredoc at solve.sh:70-103 -> environment/app/internal/posixtz/rule.go: +8 / -1 lines
- `/app/internal/posixtz/eval.go` via heredoc at solve.sh:108-162 -> environment/app/internal/posixtz/eval.go: +28 / -14 lines
- `/app/internal/tzif/leap.go` via heredoc at solve.sh:167-210 -> new file / not shipped in environment/
- `/app/internal/tzif/file.go` via heredoc at solve.sh:212-364 -> environment/app/internal/tzif/file.go: +16 / -0 lines
- `/app/internal/tzif/lookup.go` via heredoc at solve.sh:366-449 -> environment/app/internal/tzif/lookup.go: +18 / -4 lines
- `/app/internal/civil/format.go` via heredoc at solve.sh:454-540 -> environment/app/internal/civil/format.go: +34 / -6 lines
- `/app/internal/report/json.go` via heredoc at solve.sh:542-572 -> environment/app/internal/report/json.go: +9 / -6 lines
- `/app/cmd/shiftclock/at.go` via heredoc at solve.sh:574-640 -> environment/app/cmd/shiftclock/at.go: +25 / -2 lines
- `/app/cmd/shiftclock/transitions.go` via heredoc at solve.sh:642-682 -> environment/app/cmd/shiftclock/transitions.go: +4 / -3 lines

## Appendix - Tests (checks 35, 43)

- tests/test_outputs.py:72 test_us_rules_after_table_end - Zones whose tables stop in 2007/2012 follow their M3.2.0/M11.1.0 footers, including both changes each year.
- tests/test_outputs.py:77 test_last_weekday_of_month_rules - Mm.5.d selects the last such weekday of the month, including February in leap and common years.
- tests/test_outputs.py:82 test_daylight_time_spanning_new_year - Southern-hemisphere, negative-save and two-hour-save footers resolve correctly on both sides of each change.
- tests/test_outputs.py:87 test_signed_and_extended_rule_hours - RFC 8536 rule times: negative hours, hours past 24 and up to 167, with minutes, in real and synthetic zones.
- tests/test_outputs.py:95 test_julian_and_zero_based_day_rules - Jn ignores February 29 while zero-based n counts it, in both leap and common years.
- tests/test_outputs.py:100 test_transitions_listing - transitions lists every change in the UTC year range, in order, across table/footer boundaries.
- tests/test_outputs.py:112 test_zone_names_resolve_under_zoneinfo_dir - A bare zone name is looked up under SHIFTCLOCK_ZONEINFO and RFC 3339 instants are accepted.
- tests/test_outputs.py:121 test_output_lines_use_documented_key_order - Each at/transitions line is compact JSON with keys in the documented order and correct values.
- tests/test_outputs.py:142 test_leap_second_files_read_through_their_records - In files with leap-second records, Unix-second instants count leap seconds: utc/local are corrected readings a
- tests/test_outputs.py:156 test_leap_second_rfc3339_instants - RFC 3339 instants in leap-second files are UTC readings mapped through the records, including second 60.
- tests/test_outputs.py:170 test_leap_second_transitions_and_year_bounds - transitions in leap-second files reports UTC readings and bounds the years by UTC reading, not raw seconds.

## Appendix - Rubric map (checks 51, 54)

- `Agent inspects the footer TZ string of at least one file under /app/zones before editing c` (+1) -> test `test_us_rules_after_table_end` (2 shared words); instruction.md:3 (3)
- `Agent compares shiftclock output with an independent reference such as zdump on the shippe` (+3) -> test `test_zone_names_resolve_under_zoneinfo_dir` (2 shared words); instruction.md:1 (1)
- `Agent makes the end-of-DST rule time use the daylight offset in effect before the change` (+3) -> test `test_daylight_time_spanning_new_year` (3 shared words); instruction.md:1 (2)
- `Agent handles daylight time that wraps the new year for southern-hemisphere and negative-s` (+3) -> test `test_daylight_time_spanning_new_year` (7 shared words); instruction.md:1 (2)
- `Agent accepts signed rule hours and hours above 24 in the footer rule time` (+3) -> test `test_signed_and_extended_rule_hours` (3 shared words); instruction.md:3 (2)
- `Agent makes Mm.5.d select the last matching weekday of the month` (+2) -> test `test_last_weekday_of_month_rules` (4 shared words); instruction.md:1 (1)
- `Agent makes Jn skip February 29 in leap years while leaving zero-based n counting it` (+2) -> test `test_julian_and_zero_based_day_rules` (6 shared words); instruction.md:1 (1)
- `Agent builds the fixed binary and reruns it on a southern-hemisphere zone and a zone with ` (+2) -> test `test_daylight_time_spanning_new_year` (4 shared words); instruction.md:1 (1)
- `Agent reads leap-second records from the 32-bit version 1 data block as well as the 64-bit` (+2) -> test `test_leap_second_files_read_through_their_records` (5 shared words); instruction.md:3 (4)
- `Agent turns instants of a leap-second file into corrected UTC readings that show an insert` (+3) -> test `test_leap_second_files_read_through_their_records` (6 shared words); instruction.md:1 (3)
- `Agent maps RFC 3339 input and the transitions year bounds back through the leap-second rec` (+2) -> test `test_leap_second_rfc3339_instants` (5 shared words); instruction.md:3 (4)
- `Agent hardcodes zone names, footer strings or specific years in the lookup logic` (-5) -> test `test_zone_names_resolve_under_zoneinfo_dir` (2 shared words); instruction.md:3 (2)
- `Agent modifies or replaces the TZif files under /app/zones` (-3) -> test `test_us_rules_after_table_end` (1 shared words); instruction.md:1 (2)
- `Agent changes the zero-based n rule to match Python zoneinfo output` (-3) -> test `test_julian_and_zero_based_day_rules` (2 shared words); instruction.md:1 (1)
- `Agent accepts Go time package results as the reference for files with leap-second records` (-2) -> test `test_leap_second_files_read_through_their_records` (3 shared words); instruction.md:1 (3)
- `Agent adds a third-party Go module or network dependency to the build` (-2) -> test `test_us_rules_after_table_end` (0 shared words); instruction.md:3 (2)
- `Agent reruns an identical failing command three or more times in a row` (-1) -> test `test_signed_and_extended_rule_hours` (1 shared words); instruction.md:1 (1)
