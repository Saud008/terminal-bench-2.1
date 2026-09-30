# TB2.1 FINAL AUDIT — `brickmake-rule-semantics-repair`

- generated: 2026-09-26 16:28:37Z
- delivery dir (outer): `/home/snklp/TERMINAL CHECKER/tb21-final-auditor-main/extracted/brickmake-rule-semantics-repair`  · task dir (inner): `/home/snklp/TERMINAL CHECKER/tb21-final-auditor-main/extracted/brickmake-rule-semantics-repair/brickmake-rule-semantics-repair`  · layout: nested
- bundle sha16 (fresh recompute): `0babf476219b8958`
- manual answers: `(none supplied)`

## VERDICT: **NOT_READY**

Open root causes — BLOCKER: 0 · MAJOR: 1 · MINOR: 29 · REVIEW: 56  (from 86 findings — BLOCKER: 0 · MAJOR: 1 · MINOR: 29 · REVIEW: 56)
Checks not closed: 47 of 86 → [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 23, 24, 25, 26, 27, 28, 30, 31, 33, 34, 35, 36, 37, 38, 39, 43, 44, 47, 51, 53, 54, 55, 60, 70, 72, 73, 81, 83]

A task ships only with zero open findings of ANY severity and every check 0–85 at PASS, NA or INCONCLUSIVE. Severity orders the fix queue; it never excuses a finding. Findings that share a root cause are one fix and are counted once.

## Fix queue for the task author (one entry per root cause, worst first)

1. **[MAJOR] run-01: citation ['TestPatternCannotChangeCommandLineVariable', 'cli.md'] is a bare word — it does not substantiate this verdict; cite the failing assertion, a step number or a quoted multi-word output** — checks 72; findings `C72-4301f1500b`
2. **[MINOR] `brickmake-rule-semantics-repair/environment/.dockerignore` is referenced nowhere else in the bundle** — checks 17; findings `C17-744de9df9d`
3. **[MINOR] `brickmake-rule-semantics-repair/environment/app/cmd/brickmake/main.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-e46531d760`
4. **[MINOR] `brickmake-rule-semantics-repair/environment/app/examples/demo/src/value.c` is referenced nowhere else in the bundle** — checks 17; findings `C17-3c34860ff6`
5. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/cli/main.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-59a7c765b4`
6. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/cli/options.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-88492c7c6c`
7. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/db/db.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-3d3d53ab4e`
8. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/diag/diag.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-809ed76d5f`
9. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/engine/deps.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-f67c4bac28`
10. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/engine/engine.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-1137937354`
11. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/engine/implicit.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-d490debfe5`
12. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/engine/node.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-a7b9218b8a`
13. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/engine/recipe.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-41b71b7ba0`
14. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/engine/recipe_test.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-19f49b84a4`
15. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/engine/scope.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-cd77523955`
16. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/engine/update.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-73ee51b9e9`
17. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/expand/auto.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-a36c67082a`
18. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/expand/control.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-94e8181a4b`
19. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/expand/define.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-17ccc8a862`
20. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/expand/expand.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-6abf47076f`
21. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/expand/expand_test.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-a42b234acf`
22. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/expand/funcs.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-07a2457caf`
23. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/parse/cond.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-456b6b8a29`
24. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/parse/lines.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-d222d5d271`
25. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/parse/parse_test.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-fdc689590f`
26. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/parse/parser.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-7176f2ab65`
27. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/parse/rules.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-71ce6a1490`
28. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/text/words.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-e7e9c8abb1`
29. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/text/words_test.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-91f82e039e`
30. **[MINOR] `brickmake-rule-semantics-repair/environment/app/internal/vars/vars.go` is referenced nowhere else in the bundle** — checks 17; findings `C17-8b054626fa`
31. **[REVIEW] opaque file/module name `db.go`** — checks 15; findings `C15-8561f573db`
32. **[REVIEW] opaque directory name `db/`** — checks 15; findings `C15-afb69e8082`
33. **[REVIEW] `brickmake-rule-semantics-repair/environment/app/docs/functions.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:40) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it** — checks 17; findings `C17-c68ecd37bc`
34. **[REVIEW] `brickmake-rule-semantics-repair/environment/app/docs/makefiles.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:36) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it** — checks 17; findings `C17-22c9c00cbd`
35. **[REVIEW] `brickmake-rule-semantics-repair/environment/app/docs/rules.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:38, brickmake-rule-semantics-repair/environment/app/docs/makefiles.md:80, brickmake-rule-semantics-repair/environment/app/docs/updating.md:15) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it** — checks 17; findings `C17-3eb6e06ccc`
36. **[REVIEW] `brickmake-rule-semantics-repair/environment/app/docs/updating.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:39, brickmake-rule-semantics-repair/environment/app/docs/variables.md:155) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it** — checks 17; findings `C17-8b4c33ba6b`
37. **[REVIEW] unreferenced code module (176 lines, 18 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-109c27dd78`
38. **[REVIEW] unreferenced code module (134 lines, 12 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-474eb77705`
39. **[REVIEW] unreferenced code module (126 lines, 12 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-8824dc21fb`
40. **[REVIEW] unreferenced code module (70 lines, 8 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-ff990660f7`
41. **[REVIEW] unreferenced code module (89 lines, 10 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-50fd087207`
42. **[REVIEW] unreferenced code module (107 lines, 11 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-5230b79eda`
43. **[REVIEW] unreferenced code module (204 lines, 14 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-0cbf4ea984`
44. **[REVIEW] unreferenced code module (81 lines, 11 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-5d33e17ea0`
45. **[REVIEW] unreferenced code module (115 lines, 9 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-3ba6c0a436`
46. **[REVIEW] unreferenced code module (40 lines, 6 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-3f3b310df1`
47. **[REVIEW] unreferenced code module (47 lines, 4 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-7bd7ee0f90`
48. **[REVIEW] unreferenced code module (184 lines, 16 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-542766e8a6`
49. **[REVIEW] unreferenced code module (80 lines, 4 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-94bbcc27f2`
50. **[REVIEW] unreferenced code module (161 lines, 2 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-f7e19bc8cf`
51. **[REVIEW] unreferenced code module (73 lines, 4 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-4225d36edf`
52. **[REVIEW] unreferenced code module (248 lines, 11 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-0df139f2e1`
53. **[REVIEW] unreferenced code module (96 lines, 3 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-1989e71db5`
54. **[REVIEW] unreferenced code module (233 lines, 8 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-97605667c5`
55. **[REVIEW] unreferenced code module (159 lines, 4 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-958a5a7662`
56. **[REVIEW] unreferenced code module (140 lines, 7 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-8b49e8ff08`
57. **[REVIEW] unreferenced code module (110 lines, 12 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-e9797eed88`
58. **[REVIEW] unreferenced code module (200 lines, 9 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-b208fd6e55`
59. **[REVIEW] unreferenced code module (155 lines, 8 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-ccc0cbb742`
60. **[REVIEW] unreferenced code module (158 lines, 7 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-d8651f3239`
61. **[REVIEW] unreferenced code module (66 lines, 2 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-8b21d35e0a`
62. **[REVIEW] unreferenced code module (127 lines, 6 instruction-vocabulary tokens) — could it be an answer key?** — checks 18; findings `C18-e72e458037`
63. **[REVIEW] brickmake-rule-semantics-repair/environment/app/README.md (not named in instruction.md) contains 4 test literal(s) absent from instruction.md: ['./cmd/brickmake', 'LANG', 'PATH', 'append']** — checks 20; findings `C20-5ae414d117`
64. **[REVIEW] brickmake-rule-semantics-repair/environment/app/docs/functions.md (not named in instruction.md) contains 3 test literal(s) absent from instruction.md: ['stderr', 'stdout', 'stem']** — checks 20; findings `C20-c124a30719`
65. **[REVIEW] brickmake-rule-semantics-repair/environment/app/docs/makefiles.md (not named in instruction.md) contains 2 test literal(s) absent from instruction.md: ['PATH', 'append']** — checks 20; findings `C20-38733ed3ef`
66. **[REVIEW] brickmake-rule-semantics-repair/environment/app/docs/rules.md (not named in instruction.md) contains 3 test literal(s) absent from instruction.md: ['mention', 'stderr', 'stem']** — checks 20; findings `C20-8feb82a054`
67. **[REVIEW] brickmake-rule-semantics-repair/environment/app/docs/updating.md (not named in instruction.md) contains 4 test literal(s) absent from instruction.md: ['stderr', 'stdout', 'stem', 'touch']** — checks 20; findings `C20-6a9dfa24c3`
68. **[REVIEW] brickmake-rule-semantics-repair/environment/app/docs/variables.md (not named in instruction.md) contains 3 test literal(s) absent from instruction.md: ['append', 'inherit', 'stem']** — checks 20; findings `C20-8533195d17`
69. **[REVIEW] could not identify any file the solve script writes (unusual form?) — produce the delta by hand** — checks 24; findings `C24-11237ca001`
70. **[REVIEW] `test_outputs.py::test_append_semantics` fails in 3/5 runs with one identical (possibly truncated) message — the message cannot tell the runs apart; a failure count cannot say who is right: compare each run's actual output with instruction.md before calling the reference the outlier** — checks 28; findings `C28-6b35cfb774`
71. **[REVIEW] rubric.txt:1 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.08)** — checks 51; findings `C51-d6fd4200f2`
72. **[REVIEW] rubric.txt:2 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.12)** — checks 51; findings `C51-6088340410`
73. **[REVIEW] rubric.txt:3 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.64)** — checks 51; findings `C51-9ee4341b94`
74. **[REVIEW] rubric.txt:4 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_directory_relative_prerequisites, overlap 0.57)** — checks 51; findings `C51-70f6aa6786`
75. **[REVIEW] rubric.txt:5 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_mentioned_prerequisite_ought_to_exist, overlap 0.91)** — checks 51; findings `C51-7cc9dca218`
76. **[REVIEW] rubric.txt:6 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_pattern_specific_variable_order, overlap 0.42)** — checks 51; findings `C51-48f6c4480d`
77. **[REVIEW] rubric.txt:7 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_append_semantics, overlap 0.75)** — checks 51; findings `C51-d741a2c52c`
78. **[REVIEW] rubric.txt:8 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_timestamps_reread_after_recipe, overlap 0.67)** — checks 51; findings `C51-eec96e2839`
79. **[REVIEW] rubric.txt:9 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_per_goal_messages, overlap 0.88)** — checks 51; findings `C51-d7052cc075`
80. **[REVIEW] rubric.txt:10 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_prerequisite_merge_order, overlap 0.91)** — checks 51; findings `C51-6b667aff6f`
81. **[REVIEW] rubric.txt:11 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_project_builds, overlap 0.40)** — checks 51; findings `C51-d664e80151`
82. **[REVIEW] rubric.txt:12 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_timestamps_reread_after_recipe, overlap 0.30)** — checks 51; findings `C51-ea0a52e1b1`
83. **[REVIEW] rubric.txt:13 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_directory_relative_prerequisites, overlap 0.12)** — checks 51; findings `C51-541e0d3915`
84. **[REVIEW] rubric.txt:14 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.11)** — checks 51; findings `C51-389350aee8`
85. **[REVIEW] rubric.txt:15 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_pattern_specific_variable_order, overlap 0.25)** — checks 51; findings `C51-5e1ebef7f0`
86. **[REVIEW] rubric.txt:16 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_timestamps_reread_after_recipe, overlap 0.12)** — checks 51; findings `C51-8e74015278`

## Findings (worst first)

| id | sev | check | root | finding | evidence |
|---|---|---|---|---|---|
| `C72-4301f1500b` | MAJOR | 72 | `C72:not-met-unsubstantiated` | run-01: citation ['TestPatternCannotChangeCommandLineVariable', 'cli.md'] is a bare word — it does not substantiate this verdict; cite the failing assertion, a step number or a quoted multi-word output | trajectories/run-01/rubric_score.txt:15: `Agent changes the command-line interface documented in /app/docs/cli.md \| NOT MET \| 0 \| No internal/cli edit; extra work was an expand test `TestPatternCannotCh…` |
| `C17-744de9df9d` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/.dockerignore` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/.dockerignore |
| `C17-e46531d760` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/cmd/brickmake/main.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/cmd/brickmake/main.go |
| `C17-3c34860ff6` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/examples/demo/src/value.c` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/examples/demo/src/value.c |
| `C17-59a7c765b4` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/cli/main.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/cli/main.go |
| `C17-88492c7c6c` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/cli/options.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/cli/options.go |
| `C17-3d3d53ab4e` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/db/db.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/db/db.go |
| `C17-809ed76d5f` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/diag/diag.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/diag/diag.go |
| `C17-f67c4bac28` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/engine/deps.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/engine/deps.go |
| `C17-1137937354` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/engine/engine.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/engine/engine.go |
| `C17-d490debfe5` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/engine/implicit.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/engine/implicit.go |
| `C17-a7b9218b8a` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/engine/node.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/engine/node.go |
| `C17-41b71b7ba0` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/engine/recipe.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/engine/recipe.go |
| `C17-19f49b84a4` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/engine/recipe_test.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/engine/recipe_test.go |
| `C17-cd77523955` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/engine/scope.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/engine/scope.go |
| `C17-73ee51b9e9` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/engine/update.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/engine/update.go |
| `C17-a36c67082a` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/expand/auto.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/expand/auto.go |
| `C17-94e8181a4b` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/expand/control.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/expand/control.go |
| `C17-17ccc8a862` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/expand/define.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/expand/define.go |
| `C17-6abf47076f` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/expand/expand.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/expand/expand.go |
| `C17-a42b234acf` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/expand/expand_test.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/expand/expand_test.go |
| `C17-07a2457caf` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/expand/funcs.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/expand/funcs.go |
| `C17-456b6b8a29` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/parse/cond.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/parse/cond.go |
| `C17-d222d5d271` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/parse/lines.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/parse/lines.go |
| `C17-fdc689590f` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/parse/parse_test.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/parse/parse_test.go |
| `C17-7176f2ab65` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/parse/parser.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/parse/parser.go |
| `C17-71ce6a1490` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/parse/rules.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/parse/rules.go |
| `C17-e7e9c8abb1` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/text/words.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/text/words.go |
| `C17-91f82e039e` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/text/words_test.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/text/words_test.go |
| `C17-8b054626fa` | MINOR | 17 |  | `brickmake-rule-semantics-repair/environment/app/internal/vars/vars.go` is referenced nowhere else in the bundle | brickmake-rule-semantics-repair/environment/app/internal/vars/vars.go |
| `C15-8561f573db` | REVIEW | 15 |  | opaque file/module name `db.go` | brickmake-rule-semantics-repair/environment/app/internal/db/db.go |
| `C15-afb69e8082` | REVIEW | 15 |  | opaque directory name `db/` | brickmake-rule-semantics-repair/environment/app/internal/db |
| `C17-c68ecd37bc` | REVIEW | 17 |  | `brickmake-rule-semantics-repair/environment/app/docs/functions.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:40) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it | brickmake-rule-semantics-repair/environment/app/docs/functions.md |
| `C17-22c9c00cbd` | REVIEW | 17 |  | `brickmake-rule-semantics-repair/environment/app/docs/makefiles.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:36) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it | brickmake-rule-semantics-repair/environment/app/docs/makefiles.md |
| `C17-3eb6e06ccc` | REVIEW | 17 |  | `brickmake-rule-semantics-repair/environment/app/docs/rules.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:38, brickmake-rule-semantics-repair/environment/app/docs/makefiles.md:80, brickmake-rule-semantics-repair/environment/app/docs/updating.md:15) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it | brickmake-rule-semantics-repair/environment/app/docs/rules.md |
| `C17-8b4c33ba6b` | REVIEW | 17 |  | `brickmake-rule-semantics-repair/environment/app/docs/updating.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:39, brickmake-rule-semantics-repair/environment/app/docs/variables.md:155) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it | brickmake-rule-semantics-repair/environment/app/docs/updating.md |
| `C18-109c27dd78` | REVIEW | 18 |  | unreferenced code module (176 lines, 18 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/cli/main.go |
| `C18-474eb77705` | REVIEW | 18 |  | unreferenced code module (134 lines, 12 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/cli/options.go |
| `C18-8824dc21fb` | REVIEW | 18 |  | unreferenced code module (126 lines, 12 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/db/db.go |
| `C18-ff990660f7` | REVIEW | 18 |  | unreferenced code module (70 lines, 8 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/diag/diag.go |
| `C18-50fd087207` | REVIEW | 18 |  | unreferenced code module (89 lines, 10 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/engine/deps.go |
| `C18-5230b79eda` | REVIEW | 18 |  | unreferenced code module (107 lines, 11 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/engine/engine.go |
| `C18-0cbf4ea984` | REVIEW | 18 |  | unreferenced code module (204 lines, 14 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/engine/implicit.go |
| `C18-5d33e17ea0` | REVIEW | 18 |  | unreferenced code module (81 lines, 11 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/engine/node.go |
| `C18-3ba6c0a436` | REVIEW | 18 |  | unreferenced code module (115 lines, 9 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/engine/recipe.go |
| `C18-3f3b310df1` | REVIEW | 18 |  | unreferenced code module (40 lines, 6 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/engine/recipe_test.go |
| `C18-7bd7ee0f90` | REVIEW | 18 |  | unreferenced code module (47 lines, 4 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/engine/scope.go |
| `C18-542766e8a6` | REVIEW | 18 |  | unreferenced code module (184 lines, 16 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/engine/update.go |
| `C18-94bbcc27f2` | REVIEW | 18 |  | unreferenced code module (80 lines, 4 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/expand/auto.go |
| `C18-f7e19bc8cf` | REVIEW | 18 |  | unreferenced code module (161 lines, 2 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/expand/control.go |
| `C18-4225d36edf` | REVIEW | 18 |  | unreferenced code module (73 lines, 4 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/expand/define.go |
| `C18-0df139f2e1` | REVIEW | 18 |  | unreferenced code module (248 lines, 11 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/expand/expand.go |
| `C18-1989e71db5` | REVIEW | 18 |  | unreferenced code module (96 lines, 3 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/expand/expand_test.go |
| `C18-97605667c5` | REVIEW | 18 |  | unreferenced code module (233 lines, 8 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/expand/funcs.go |
| `C18-958a5a7662` | REVIEW | 18 |  | unreferenced code module (159 lines, 4 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/parse/cond.go |
| `C18-8b49e8ff08` | REVIEW | 18 |  | unreferenced code module (140 lines, 7 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/parse/lines.go |
| `C18-e9797eed88` | REVIEW | 18 |  | unreferenced code module (110 lines, 12 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/parse/parse_test.go |
| `C18-b208fd6e55` | REVIEW | 18 |  | unreferenced code module (200 lines, 9 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/parse/parser.go |
| `C18-ccc0cbb742` | REVIEW | 18 |  | unreferenced code module (155 lines, 8 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/parse/rules.go |
| `C18-d8651f3239` | REVIEW | 18 |  | unreferenced code module (158 lines, 7 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/text/words.go |
| `C18-8b21d35e0a` | REVIEW | 18 |  | unreferenced code module (66 lines, 2 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/text/words_test.go |
| `C18-e72e458037` | REVIEW | 18 |  | unreferenced code module (127 lines, 6 instruction-vocabulary tokens) — could it be an answer key? | brickmake-rule-semantics-repair/environment/app/internal/vars/vars.go |
| `C20-5ae414d117` | REVIEW | 20 |  | brickmake-rule-semantics-repair/environment/app/README.md (not named in instruction.md) contains 4 test literal(s) absent from instruction.md: ['./cmd/brickmake', 'LANG', 'PATH', 'append'] | brickmake-rule-semantics-repair/environment/app/README.md |
| `C20-c124a30719` | REVIEW | 20 |  | brickmake-rule-semantics-repair/environment/app/docs/functions.md (not named in instruction.md) contains 3 test literal(s) absent from instruction.md: ['stderr', 'stdout', 'stem'] | brickmake-rule-semantics-repair/environment/app/docs/functions.md |
| `C20-38733ed3ef` | REVIEW | 20 |  | brickmake-rule-semantics-repair/environment/app/docs/makefiles.md (not named in instruction.md) contains 2 test literal(s) absent from instruction.md: ['PATH', 'append'] | brickmake-rule-semantics-repair/environment/app/docs/makefiles.md |
| `C20-8feb82a054` | REVIEW | 20 |  | brickmake-rule-semantics-repair/environment/app/docs/rules.md (not named in instruction.md) contains 3 test literal(s) absent from instruction.md: ['mention', 'stderr', 'stem'] | brickmake-rule-semantics-repair/environment/app/docs/rules.md |
| `C20-6a9dfa24c3` | REVIEW | 20 |  | brickmake-rule-semantics-repair/environment/app/docs/updating.md (not named in instruction.md) contains 4 test literal(s) absent from instruction.md: ['stderr', 'stdout', 'stem', 'touch'] | brickmake-rule-semantics-repair/environment/app/docs/updating.md |
| `C20-8533195d17` | REVIEW | 20 |  | brickmake-rule-semantics-repair/environment/app/docs/variables.md (not named in instruction.md) contains 3 test literal(s) absent from instruction.md: ['append', 'inherit', 'stem'] | brickmake-rule-semantics-repair/environment/app/docs/variables.md |
| `C24-11237ca001` | REVIEW | 24 |  | could not identify any file the solve script writes (unusual form?) — produce the delta by hand | brickmake-rule-semantics-repair/solution/solve.sh |
| `C28-6b35cfb774` | REVIEW | 28 | `C28:fails-run-03+run-04+run-05` | `test_outputs.py::test_append_semantics` fails in 3/5 runs with one identical (possibly truncated) message — the message cannot tell the runs apart; a failure count cannot say who is right: compare each run's actual output with instruction.md before calling the reference the outlier | run-03, run-04, run-05: AssertionError: appe... |
| `C51-d6fd4200f2` | REVIEW | 51 |  | rubric.txt:1 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.08) | rubric.txt:1: `Agent reads the relevant sections of /app/docs (rules.md, variables.md, updating.md) before changing engine or expand code, +2` |
| `C51-6088340410` | REVIEW | 51 |  | rubric.txt:2 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.12) | rubric.txt:2: `Agent reproduces at least one reported symptom with a scratch makefile before editing, +2` |
| `C51-9ee4341b94` | REVIEW | 51 |  | rubric.txt:3 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.64) | rubric.txt:3: `Agent fixes pattern-rule selection so the stem length includes the directory part of a directory-relative match, +3` |
| `C51-70f6aa6786` | REVIEW | 51 |  | rubric.txt:4 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_directory_relative_prerequisites, overlap 0.57) | rubric.txt:4: `Agent limits the directory prefix of a directory-relative match to prerequisites that contain '%', +2` |
| `C51-7cc9dca218` | REVIEW | 51 |  | rubric.txt:5 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_mentioned_prerequisite_ought_to_exist, overlap 0.91) | rubric.txt:5: `Agent treats a prerequisite that is mentioned anywhere in the makefile as one that ought to exist in the first implicit-rule pass, +2` |
| `C51-48f6c4480d` | REVIEW | 51 |  | rubric.txt:6 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_pattern_specific_variable_order, overlap 0.42) | rubric.txt:6: `Agent orders pattern-specific variables by pattern length and places the file's own pattern set before the inherited parent context, +3` |
| `C51-d741a2c52c` | REVIEW | 51 |  | rubric.txt:7 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_append_semantics, overlap 0.75) | rubric.txt:7: `Agent makes '+=' on a simply expanded variable expand the added text at once and keeps a target's own '+=' as an in-set append, +3` |
| `C51-eec96e2839` | REVIEW | 51 |  | rubric.txt:8 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_timestamps_reread_after_recipe, overlap 0.67) | rubric.txt:8: `Agent re-reads a target's time after its recipe runs instead of marking it as newest, +2` |
| `C51-d7052cc075` | REVIEW | 51 |  | rubric.txt:9 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_per_goal_messages, overlap 0.88) | rubric.txt:9: `Agent reports "up to date" / "Nothing to be done" per goal based only on commands run for that goal, +2` |
| `C51-6b667aff6f` | REVIEW | 51 |  | rubric.txt:10 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_prerequisite_merge_order, overlap 0.91) | rubric.txt:10: `Agent combines a target's prerequisites from several rules with the recipe rule's list first, then the other rules in makefile order, +2` |
| `C51-d664e80151` | REVIEW | 51 |  | rubric.txt:11 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_project_builds, overlap 0.40) | rubric.txt:11: `Agent rebuilds brickmake and compares its output against GNU make or the documented examples after the fixes, +3` |
| `C51-ea0a52e1b1` | REVIEW | 51 |  | rubric.txt:12 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_timestamps_reread_after_recipe, overlap 0.30) | rubric.txt:12: `Agent makes brickmake shell out to or embed GNU make instead of fixing its own logic, -5` |
| `C51-541e0d3915` | REVIEW | 51 |  | rubric.txt:13 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_directory_relative_prerequisites, overlap 0.12) | rubric.txt:13: `Agent special-cases the file names or flags quoted in the instruction or docs examples, -5` |
| `C51-389350aee8` | REVIEW | 51 |  | rubric.txt:14 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.11) | rubric.txt:14: `Agent edits /app/docs to match the existing behavior instead of fixing the code, -3` |
| `C51-5e1ebef7f0` | REVIEW | 51 |  | rubric.txt:15 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_pattern_specific_variable_order, overlap 0.25) | rubric.txt:15: `Agent changes the command-line interface documented in /app/docs/cli.md, -3` |
| `C51-8e74015278` | REVIEW | 51 |  | rubric.txt:16 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_timestamps_reread_after_recipe, overlap 0.12) | rubric.txt:16: `Agent reruns an identical failing command three or more times in a row, -1` |

## Check status (0–85)

| # | sec | mode | status | title |
|---|---|---|---|---|
| 0 | A | ASSIST | **REVIEW** | Prompt is human-written, absolute backticked paths, outputs named, what-not-how, <1500 tokens |
| 1 | A | ASSIST | **REVIEW** | Every stated requirement is exercised by ≥1 test (sentence-by-sentence cross-map) |
| 2 | A | ASSIST | **REVIEW** | Every requirement a test enforces is stated (no unstated graded rule) |
| 3 | A | ASSIST | **REVIEW** | No sentence prescribes an internal implementation step (how vs what) |
| 4 | A | MANUAL | **REVIEW** | Interface-contract sentences (paths, flags, exit codes, schema) are graded as interfaces, not nudges |
| 5 | A | AUTO | **PASS** | No grader/test-suite/verifier/pytest/pipeline terms in instruction.md |
| 6 | A | ASSIST | **REVIEW** | Every numeric constant/tolerance/threshold in instruction.md matches tests/ byte-for-byte |
| 7 | A | ASSIST | **REVIEW** | Every path instruction.md names exists at that exact path in environment/ (after build) |
| 8 | A | ASSIST | **REVIEW** | Output schemas in prose are checked with the same exactness in tests/ (and reference honours it) |
| 9 | A | ASSIST | **REVIEW** | instruction.md does not contradict itself between two sentences on the same rule |
| 10 | A | ASSIST | **REVIEW** | Prompt does not narrate each planted defect's exact mechanism (symptom ok, literal fix not ok) |
| 11 | B | ASSIST | **REVIEW** | Every file under environment/ is required (read each through) |
| 12 | B | AUTO | **PASS** | No comment under environment/ or solution/ narrates the bug/fix/intent (literal grep) |
| 13 | B | ASSIST | **REVIEW** | No comment restates/paraphrases an instruction.md sentence (n-gram echo scan) |
| 14 | B | ASSIST | **REVIEW** | No lore/notes/history doc itemises the planted defects 1:1 |
| 15 | B | ASSIST | **REVIEW** | No senseless/obscure file, module or function names (k7, t2, qp7 …) |
| 16 | B | MANUAL | **REVIEW** | No function/module name mislabels what the code does |
| 17 | B | AUTO | **FAIL** | No dead/orphaned/unreferenced file under environment/ (basename grep across bundle) |
| 18 | B | ASSIST | **REVIEW** | No unused helper already implements the core capability (answer-key module) |
| 19 | B | MANUAL | **REVIEW** | Docs instruction.md names as authoritative are consistent with instruction.md |
| 20 | B | ASSIST | **REVIEW** | No un-named environment doc silently holds a rule the tests grade |
| 21 | B | AUTO | **PASS** | Vendored binaries/archives carry no authoring-machine metadata |
| 22 | B | AUTO | **PASS** | Dockerfile never COPY/ADDs solution/ or tests/ (directly or via a parent dir) |
| 23 | B | ASSIST | **REVIEW** | Any decoy is reachable/inspectable and never labelled as a decoy |
| 24 | C | ASSIST | **REVIEW** | solve.sh diffed file-by-file against environment/ → exact delta list |
| 25 | C | MANUAL | **MISSING** | Every touched file maps to a real defect/capability instruction.md asks for |
| 26 | C | MANUAL | **REVIEW** | No delta changes graded behaviour instruction.md never asks for (scope creep / undisclosed requirement) |
| 27 | C | MANUAL | **REVIEW** | Reference output independently verified CORRECT (not merely test-consistent) — MANDATORY for named math/algorithmic structures |
| 28 | C | ASSIST | **REVIEW** | If agent trajectories converge on a value ≠ reference, check whether the reference is the outlier |
| 29 | C | AUTO | **PASS** | solution/ has no orphan files solve.sh does not reference |
| 30 | C | ASSIST | **REVIEW** | Per-file ablation: reverting each fixed file alone produces the expected specific test failures |
| 31 | C | MANUAL | **REVIEW** | Oracle builds and runs cleanly from a COLD image build under DOCKER_DEFAULT_PLATFORM=linux/amd64 |
| 32 | D | AUTO | **PASS** | Zero individual tests pass under NOP (read nop-1/nop-2 ctrf.json test by test) |
| 33 | D | ASSIST | **REVIEW** | Regression-guard tests are coupled to a real-behaviour assertion in the same function |
| 34 | D | MANUAL | **REVIEW** | NOP-passable tests are fixed by COUPLING, never by deleting the guard |
| 35 | D | MANUAL | **REVIEW** | Every test's assertions read in full and match its name/docstring |
| 36 | D | ASSIST | **REVIEW** | No test's expected value is computed by agent-editable code |
| 37 | D | ASSIST | **REVIEW** | Test fixtures are not read from an agent-modifiable path that also feeds the expected side |
| 38 | D | ASSIST | **REVIEW** | Every held-out/hidden scenario genuinely changes the graded outcome vs the public one |
| 39 | D | ASSIST | **REVIEW** | Stated exactness rules are enforced literally (set equality) and the reference satisfies them |
| 40 | D | AUTO | **PASS** | Every stated numeric tolerance equals the literal compiled into the assertions |
| 41 | D | AUTO | **PASS** | No string-obfuscation tricks in tests ("a" + "b" concatenation to defeat grep) |
| 42 | D | AUTO | **PASS** | No dead/unused test-only code (unused imports, helpers no test calls) |
| 43 | D | MANUAL | **REVIEW** | Test names accurately describe what each test checks |
| 44 | D | ASSIST | **REVIEW** | Every fail-closed/rejection test also runs a known-good positive control in the same function |
| 45 | D | AUTO | **PASS** | Test count in every ctrf.json equals tests collected from the current tests/ tree |
| 46 | E/F | AUTO | **PASS** | schema_version = "1.1" is the literal first line of task.toml |
| 47 | E/F | ASSIST | **REVIEW** | description/keywords/[[task.authors]]/category/tags present, accurate, not placeholder/stale |
| 48 | E/F | AUTO | **PASS** | All timeouts (agent/verifier/…) = 7200 |
| 49 | E/F | AUTO | **PASS** | No [reference_pattern] or other pipeline/authoring metadata in task.toml |
| 50 | E/F | AUTO | **PASS** | allow_internet = true and no contradicting offline instruction |
| 51 | E/F | ASSIST | **REVIEW** | Every rubric line maps to a real test or instruction (nothing grades ungraded behaviour) |
| 52 | E/F | AUTO | **PASS** | Every rubric line is `Agent <does X>, +N` / `, -N`; no headers/blank lines/asides |
| 53 | E/F | MANUAL | **REVIEW** | No two rubric lines are mutually unsatisfiable |
| 54 | E/F | ASSIST | **REVIEW** | No rubric line double-counts the same behaviour under two criteria |
| 55 | E/F | ASSIST | **REVIEW** | rubric.txt point budget matches rubric_score.txt MET/NOT MET arithmetic (verify one by hand) |
| 56 | E/F | AUTO | **PASS** | Rubric cites no mechanism/path absent from the shipped environment |
| 57 | H | AUTO | **PASS** | oracle-nop-evidence/ is exactly {oracle-1,2,3,nop-1,2}/{ctrf.json,reward.txt,test-stdout.txt} |
| 58 | H | AUTO | **PASS** | oracle-1/2/3 each reward 1.0 with every test passed (test-by-test) |
| 59 | H | AUTO | **PASS** | nop-1/2 each reward 0.0 with every test explicitly 'failed' (not error/skipped) |
| 60 | H | ASSIST | **REVIEW** | NOP failures are genuine assertion mismatches, not import/crash/infra errors |
| 61 | H | AUTO | **PASS** | Evidence mtimes newer than every graded file (tests/, environment/, solution/, instruction.md) |
| 62 | H | AUTO | **PASS** | Duplication check on the evidence set (3 independent oracle passes, 2 independent NOP fails) |
| 63 | G | AUTO | **PASS** | SUMMARY.txt is exactly 2 lines: slug+sha+model+reasoning_effort, then the 5-run reward array |
| 64 | G | AUTO | **PASS** | Every rubric_score.txt is pure data + evidence citations (no note:/Summary:/process narration) |
| 65 | G | AUTO | **PASS** | SUMMARY.txt reward array == each run's verifier/reward.txt == its ctrf.json outcome, in order |
| 66 | G | AUTO | **PASS** | SUMMARY.txt bundle sha == fresh recompute from disk (find\|sort\|shasum pipeline) |
| 67 | G | AUTO | **PASS** | Newest graded mtime is OLDER than every trajectories/run-*/ and every evidence ctrf.json |
| 68 | G | AUTO | **PASS** | oracle-1/2/3 are three independent executions (timestamps, addresses, hashes differ) |
| 69 | G | AUTO | **PASS** | nop-1/2 are two independent executions |
| 70 | G | MANUAL | **REVIEW** | For every failing run the real failure was read from trajectory.json + test-stdout.txt and matches rubric_score.txt's claim |
| 71 | G | AUTO | **PASS** | The 5 rubric_score.txt files are not byte-identical / near-identical copies |
| 72 | G | ASSIST | **FAIL** | Every NOT MET / negative verdict cites a line, function or quoted value found in THAT run's own trajectory/stdout |
| 73 | G | MANUAL | **REVIEW** | MET verdicts spot-checked against the run's own trajectory (no over-claimed MET) |
| 74 | G | AUTO | **PASS** | PII scrub clean across every trajectory file (/Users/, /private/tmp/, /home/<user>, \bstb\b) |
| 75 | G | AUTO | **PASS** | config.json trials_dir / task.path / trial_uri scrubbed to /terminal-bench2.1/<slug> form |
| 76 | G | AUTO | **PASS** | result.json model fields left at raw captured form (not hand-edited to match config.json) |
| 77 | G | AUTO | **PASS** | Every agent/ folder has the same canonical file set (api-calls.jsonl, recording.cast, *.pane, trajectory.json) |
| 78 | G | AUTO | **PASS** | Every verifier/ has ctrf.json, reward.txt, test-stdout.txt; reward.txt matches ctrf outcome |
| 79 | G | AUTO | **PASS** | reasoning_effort == "xhigh" on every one of the 5 runs individually |
| 80 | G | AUTO | **PASS** | No run's result.json has exception_info populated (infra error invalidates the reward) |
| 81 | G | ASSIST | **REVIEW** | Reward-hacking scan per trajectory: no /tests, test_outputs.py, ctrf/reward, /opt/verifier, solution/ access; no hand-written outputs; no truncation; genuine completion |
| 82 | G | AUTO | **PASS** | After any k=5 rerun the six artefacts moved together (5 run dirs, SUMMARY, 5 rubric_scores, task.toml estimates, sha, fresh PII grep) |
| 83 | I | MANUAL | **REVIEW** | No manufactured difficulty — classify the difficulty SOURCE (reasoning/engineering vs obscurity, transcription, decoys, hidden rules, compliance walls) |
| 84 | I | AUTO | **PASS** | Delivery structure exact: <slug>/{ <slug>/{instruction.md,task.toml,environment,solution,tests}, rubric.txt, oracle-nop-evidence/, trajectories/ } — nothing else, no junk, no extra wrapper |
| 85 | I | AUTO | **PASS** | FINAL post-every-edit grep for \bstb\b, /Users/, /private/tmp/, /home/<user> across the ENTIRE bundle (last step before zipping) |

## Detail

### SECTION A — INSTRUCTION.MD

#### 0. Prompt is human-written, absolute backticked paths, outputs named, what-not-how, <1500 tokens
mode: ASSIST · status: **REVIEW**
- note: approx token count: 347 (words=233, chars=1389)
<details><summary>worksheet (read before answering)</summary>

```
Human authorship, 'what not how', and that every expected output file is named cannot be decided by script — read the whole prompt once, top to bottom, and answer with the output-file list you found.
Output files named in instruction.md (regex): /app/cmd/brickmake, /app/docs, /app/docs/cli.md
```
</details>

#### 1. Every stated requirement is exercised by ≥1 test (sentence-by-sentence cross-map)
mode: ASSIST · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
REQUIREMENT → BEST-MATCHING TEST (jaccard on tokens; 0.00 = no test shares vocabulary — investigate)
instruction.md:3 [0.12 → brickmake-rule-semantics-repair/tests/test_outputs.py::test_per_goal_messages]   <-- WEAK/NO COVERAGE
    - in our net build dir `make -r -R` compiles `sock.o` with `-O2 -fPIC -DNET`, brickmake gets the flags wrong - a codegen step whose recipe leaves its output alone when nothing changed still makes bric
instruction.md:9 [0.19 → brickmake-rule-semantics-repair/tests/test_outputs.py::test_project_builds]   <-- WEAK/NO COVERAGE
    That's probably not the full list. brickmake is supposed to act exactly like GNU make 4.3 run as `make -r -R` for everything described in `/app/docs`: same recipe lines, messages, exit codes and files
instruction.md:11 [0.50 → brickmake-rule-semantics-repair/tests/test_outputs.py::test_project_builds]
    This container only has brickmake, GNU make isn't installed.
instruction.md:11 [0.20 → brickmake-rule-semantics-repair/tests/test_outputs.py::test_pattern_specific_variable_order]   <-- WEAK/NO COVERAGE
    Keep it Go standard library only; we build `/app/cmd/brickmake` with plain `go build`, and the command-line interface in `/app/docs/cli.md` shouldn't change.
3 requirement sentence(s) with weak lexical coverage — each needs a manual mapping or is a finding.
```
</details>

#### 2. Every requirement a test enforces is stated (no unstated graded rule)
mode: ASSIST · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Literal strings/paths in tests/ that do not occur in instruction.md or any environment/ doc (candidates for unstated requirements — expected-output keys, filenames, exact messages):
  brickmake-rule-semantics-repair/tests/harness.py:1: 'Plays a build scenario in a scratch directory and records what the build tool printed.'
  brickmake-rule-semantics-repair/tests/harness.py:9: 'HOME'
  brickmake-rule-semantics-repair/tests/harness.py:9: 'LC_ALL'
  brickmake-rule-semantics-repair/tests/harness.py:9: '/usr/local/bin:/usr/bin:/bin'
  brickmake-rule-semantics-repair/tests/harness.py:9: '/nonexistent'
  brickmake-rule-semantics-repair/tests/harness.py:26: 'write'
  brickmake-rule-semantics-repair/tests/harness.py:29: 'utf-8'
  brickmake-rule-semantics-repair/tests/harness.py:49: 'unknown step'
  brickmake-rule-semantics-repair/tests/test_outputs.py:15: '/tmp/brickmake-verify'
  brickmake-rule-semantics-repair/tests/test_outputs.py:31: 'go build failed:'
  brickmake-rule-semantics-repair/tests/test_outputs.py:20: 'session'
  brickmake-rule-semantics-repair/tests/test_outputs.py:37: 'no scenarios for'
  brickmake-rule-semantics-repair/tests/test_outputs.py:59: 'dirs'
  brickmake-rule-semantics-repair/tests/test_outputs.py:71: 'restat'
  brickmake-rule-semantics-repair/tests/test_outputs.py:83: 'patvars'
  brickmake-rule-semantics-repair/tests/test_outputs.py:101: 'merge'
  brickmake-rule-semantics-repair/tests/test_outputs.py:107: 'project'
  brickmake-rule-semantics-repair/tests/test_outputs.py:16: 'cases.json'
  brickmake-rule-semantics-repair/tests/test_outputs.py:25: '/usr/local/go/bin/go'
  brickmake-rule-semantics-repair/tests/test_outputs.py:41: 'steps'
  brickmake-rule-semantics-repair/tests/test_outputs.py:36: 'group'
  brickmake-rule-semantics-repair/tests/test_outputs.py:42: 'expect'
  brickmake-rule-semantics-repair/tests/test_outputs.py:46: ': expected'
  brickmake-rule-semantics-repair/tests/test_outputs.py:46: 'results, got'
  brickmake-rule-semantics-repair/tests/test_outputs.py:44: 'result #'
  brickmake-rule-semantics-repair/tests/test_outputs.py:44: 'expected:'
  brickmake-rule-semantics-repair/tests/test_outputs.py:44: 'actual:'
For each: is it an interface contract the agent could only know from instruction.md/docs? If the test needs it and the prose never says it → BLOCKER.
```
</details>

#### 3. No sentence prescribes an internal implementation step (how vs what)
mode: ASSIST · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Heuristic only. Read every sentence yourself; the regexes catch algorithm names, data-structure choices and line-level edits, not every prescription. Every flagged sentence must be either reworded as a 'what' (graded behaviour unchanged) or classified as an interface contract under check 4.
```
</details>

#### 4. Interface-contract sentences (paths, flags, exit codes, schema) are graded as interfaces, not nudges
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Sentences that look like interface contracts (paths / flags / exit codes / schema words):
  instruction.md:3: - in our net build dir `make -r -R` compiles `sock.o` with `-O2 -fPIC -DNET`, brickmake gets the flags wrong - a codegen step whose recipe leaves its output alo
  instruction.md:9: That's probably not the full list. brickmake is supposed to act exactly like GNU make 4.3 run as `make -r -R` for everything described in `/app/docs`: same reci
For each: confirm a test asserts against it AS an interface (path opened, flag passed, exit code compared). If it only steers the internal fix, it is a check-3 violation.
```
</details>

#### 5. No grader/test-suite/verifier/pytest/pipeline terms in instruction.md
mode: AUTO · status: **PASS**
- note: zero hits for grader/test suite/verifier/pytest//tests//opt/verifier/ctrf/reward.txt/rubric/harbor/oracle

#### 6. Every numeric constant/tolerance/threshold in instruction.md matches tests/ byte-for-byte
mode: ASSIST · status: **REVIEW**
- note: instruction tolerances: -; test tolerance literals near tolerance keywords: -
<details><summary>worksheet (read before answering)</summary>

```
Confirm every REVIEW number above by grep; a doc/test mismatch on any tolerance or threshold is a BLOCKER.
```
</details>

#### 7. Every path instruction.md names exists at that exact path in environment/ (after build)
mode: ASSIST · status: **REVIEW**
- note: /app/docs → brickmake-rule-semantics-repair/environment/app/docs (exists)
- note: /app/cmd/brickmake → brickmake-rule-semantics-repair/environment/app/cmd/brickmake (exists)
- note: /app/docs/cli.md → brickmake-rule-semantics-repair/environment/app/docs/cli.md (exists)
- note: every referenced path either resolves to a shipped file or is an agent-written output
- note: script found nothing; a manual PASS with evidence is still required to close this check
<details><summary>worksheet (read before answering)</summary>

```
Dockerfile COPY/ADD map: app/→/app/ (WORKDIR /app)
```
</details>

#### 8. Output schemas in prose are checked with the same exactness in tests/ (and reference honours it)
mode: ASSIST · status: **REVIEW**
- note: no exactness phrasing in prose → nothing to reconcile; still confirm any schema listed in prose is asserted key-by-key
<details><summary>worksheet (read before answering)</summary>

```
No 'exactly these keys / no other fields / unique and sorted' phrasing found in instruction.md or environment docs.
Also confirm the reference solution's actual output honours the 'exactly' reading (run solve.sh output through a strict key-set diff).
```
</details>

#### 9. instruction.md does not contradict itself between two sentences on the same rule
mode: ASSIST · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Sentence pairs sharing ≥45% vocabulary (same rule stated twice — read both and confirm one reading):
  (no lexically similar sentence pairs — still read for once-vs-recurring / ordering / tie-break wording)
```
</details>

#### 10. Prompt does not narrate each planted defect's exact mechanism (symptom ok, literal fix not ok)
mode: ASSIST · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Compare each 'what's wrong' sentence against the solve.sh delta (check 24 worksheet): if the sentence could be pasted as the commit message of the fix, it's narrating the mechanism.
```
</details>

### SECTION B — ENVIRONMENT/

#### 11. Every file under environment/ is required (read each through)
mode: ASSIST · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
environment/ inventory (size, lines, references: real + prose/comment-only — see check 17):
  brickmake-rule-semantics-repair/environment/.dockerignore  195B  lines=18  refs=0+0
  brickmake-rule-semantics-repair/environment/Dockerfile  833B  lines=28  refs=1+0
  brickmake-rule-semantics-repair/environment/app/README.md  1649B  lines=41  refs=0+0
  brickmake-rule-semantics-repair/environment/app/go.mod  26B  lines=3  refs=0+0
  brickmake-rule-semantics-repair/environment/app/cmd/brickmake/main.go  227B  lines=13  refs=0+0
  brickmake-rule-semantics-repair/environment/app/docs/cli.md  1257B  lines=32  refs=1+1
  brickmake-rule-semantics-repair/environment/app/docs/functions.md  2337B  lines=50  refs=0+1
  brickmake-rule-semantics-repair/environment/app/docs/makefiles.md  3435B  lines=90  refs=0+1
  brickmake-rule-semantics-repair/environment/app/docs/rules.md  5895B  lines=143  refs=0+4
  brickmake-rule-semantics-repair/environment/app/docs/updating.md  3980B  lines=109  refs=0+2
  brickmake-rule-semantics-repair/environment/app/docs/variables.md  6179B  lines=166  refs=1+3
  brickmake-rule-semantics-repair/environment/app/examples/demo/Makefile  627B  lines=31  refs=44+6
  brickmake-rule-semantics-repair/environment/app/examples/demo/include/demo.h  61B  lines=6  refs=3+0
  brickmake-rule-semantics-repair/environment/app/examples/demo/src/main.c  73B  lines=3  refs=12+0
  brickmake-rule-semantics-repair/environment/app/examples/demo/src/value.c  55B  lines=3  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/cli/main.go  4575B  lines=176  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/cli/options.go  2665B  lines=134  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/db/db.go  3004B  lines=126  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/diag/diag.go  1562B  lines=70  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/engine/deps.go  2234B  lines=89  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/engine/engine.go  2079B  lines=107  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/engine/implicit.go  5086B  lines=204  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/engine/node.go  1409B  lines=81  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/engine/recipe.go  2242B  lines=115  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/engine/recipe_test.go  1034B  lines=40  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/engine/scope.go  1184B  lines=47  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/engine/update.go  4014B  lines=184  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/expand/auto.go  1665B  lines=80  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/expand/control.go  3529B  lines=161  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/expand/define.go  2872B  lines=73  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/expand/expand.go  5780B  lines=248  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/expand/expand_test.go  3187B  lines=96  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/expand/funcs.go  5981B  lines=233  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/parse/cond.go  3633B  lines=159  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/parse/lines.go  3299B  lines=140  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/parse/parse_test.go  2860B  lines=110  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/parse/parser.go  5027B  lines=200  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/parse/rules.go  3931B  lines=155  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/text/words.go  3749B  lines=158  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/text/words_test.go  1695B  lines=66  refs=0+0
  brickmake-rule-semantics-repair/environment/app/internal/vars/vars.go  2006B  lines=127  refs=0+0
Answer only after opening every file. Any file whose purpose you cannot state in one sentence is a finding.
```
</details>

#### 12. No comment under environment/ or solution/ narrates the bug/fix/intent (literal grep)
mode: AUTO · status: **PASS**
- note: zero hits across 42 text files for TODO/BUG/FIXME/planted/deliberate/for-the-grader/for-the-test/hint/the-fix

#### 13. No comment restates/paraphrases an instruction.md sentence (n-gram echo scan)
mode: ASSIST · status: **REVIEW**
- note: no comment shares ≥40% vocabulary with any instruction sentence
<details><summary>worksheet (read before answering)</summary>

```
Also read the comment nearest every location solve.sh changes (check 24 delta) and cross-check it by hand — a paraphrase can evade token overlap.
```
</details>

#### 14. No lore/notes/history doc itemises the planted defects 1:1
mode: ASSIST · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
solve.sh touches ~0 file(s) (check 24). Docs under environment/ with bullet lists:
  brickmake-rule-semantics-repair/environment/app/README.md: 6 bullet(s)
      - `docs/makefiles.md` - how makefiles are read
      - `docs/variables.md` - flavors, appending, target- and pattern-specific variables
      - `docs/rules.md` - explicit, static pattern and pattern rules; implicit rule search
      - `docs/updating.md` - when targets are remade and what brickmake prints
      - `docs/functions.md` - supported functions
      - `docs/cli.md` - command line
  brickmake-rule-semantics-repair/environment/app/docs/rules.md: 5 bullet(s)
      1. A rule applies if each of its prerequisites (normal and order-only)
      2. If no rule applies, the rules are tried again, and a prerequisite that
      - A missing intermediate file does not by itself make its dependent out of
      - An intermediate file is made only when its dependent has to be remade,
      - Intermediate files made during the run are deleted at the end, printing
  brickmake-rule-semantics-repair/environment/app/docs/updating.md: 11 bullet(s)
      1. runs implicit rule search if the target has no recipe (`rules.md`);
      2. considers each prerequisite in order (normal and order-only; intermediate
      3. decides whether the target is out of date;
      4. if it is, runs its recipe.
      - it is phony;
      - it does not exist;
      - `-B` was given;
      - a normal prerequisite is phony, does not exist (after it was considered),
      - `brickmake: Nothing to be done for 'GOAL'.` if the goal is phony or has no
      - `brickmake: 'GOAL' is up to date.` otherwise.
      2. With `-k`, brickmake continues with the other prerequisites and goals;
  brickmake-rule-semantics-repair/environment/app/docs/variables.md: 9 bullet(s)
      - recursive: the unexpanded `text` is added to the unexpanded value, so it
      - simple: `text` is expanded **now** and the result is added to the stored
      - `=` and `:=` define the variable for the target; `:=` expands the value
      - `?=` defines the variable for the target only if no variable of that name
      - `+=` extends the target's own earlier definition if the same target
      1. the file's own target-specific variables,
      2. the file's pattern-specific set,
      3. the variables of the target that first asked for the file (its own
      4. the global variables.
```
</details>

#### 15. No senseless/obscure file, module or function names (k7, t2, qp7 …)
mode: ASSIST · status: **REVIEW**
- **[REVIEW]** `C15-8561f573db` opaque file/module name `db.go`
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/db/db.go
- **[REVIEW]** `C15-afb69e8082` opaque directory name `db/`
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/db

#### 16. No function/module name mislabels what the code does
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Function/class inventory (name → file:line). For every name in a file solve.sh touches, read the body and confirm the name describes the behaviour:
  brickmake-rule-semantics-repair/environment/app/cmd/brickmake/main.go: main@11
  brickmake-rule-semantics-repair/environment/app/examples/demo/src/main.c: main@3
  brickmake-rule-semantics-repair/environment/app/examples/demo/src/value.c: demo_value@3
  brickmake-rule-semantics-repair/environment/app/internal/cli/main.go: Main@36, errText@122, initVariables@134, environment@154
  brickmake-rule-semantics-repair/environment/app/internal/cli/options.go: Parse@42, flag@107, addOperand@128
  brickmake-rule-semantics-repair/environment/app/internal/db/db.go: RecipeRule@48, New@85, Lookup@88, Enter@91, sameWords@101, AddPatternRule@116
  brickmake-rule-semantics-repair/environment/app/internal/diag/diag.go: Valid@25, String@27, Error@40, Failf@48, Warn@53, Say@63, Err@68
  brickmake-rule-semantics-repair/environment/app/internal/engine/deps.go: ruleWords@11, depsOf@33, autoVars@67
  brickmake-rule-semantics-repair/environment/app/internal/engine/engine.go: New@30, node@34, Run@45, removeIntermediates@82
  brickmake-rule-semantics-repair/environment/app/internal/engine/implicit.go: fullStem@33, candidates@39, prereqs@74, oughtToExist@97, findImplicit@109, newMatch@160, implicitFor@171
  brickmake-rule-semantics-repair/environment/app/internal/engine/node.go: statFile@36, name@73, stat@75, hasRule@79
  brickmake-rule-semantics-repair/environment/app/internal/engine/recipe.go: prefixes@21, allForced@39, run@54, exec@90, ShellOutput@109
  brickmake-rule-semantics-repair/environment/app/internal/engine/recipe_test.go: TestPrefixes@9, TestAllForced@30
  brickmake-rule-semantics-repair/environment/app/internal/engine/scope.go: patternSet@12, scope@38
  brickmake-rule-semantics-repair/environment/app/internal/engine/update.go: outdated@11, noRule@18, fail@30, update@39, checkIntermediate@111, remake@147, refresh@178
  brickmake-rule-semantics-repair/environment/app/internal/expand/auto.go: IsAutomatic@25, raw@32, Value@54
  brickmake-rule-semantics-repair/environment/app/internal/expand/control.go: fnForeach@13, fnIf@30, fnOr@40, fnAnd@49, fnCall@61, lookupNamed@101, fnOrigin@107, fnFlavor@118, fnValue@126, fnInfo@139, fnWarning@144, fnError@149, fnShell@154
  brickmake-rule-semantics-repair/environment/app/internal/expand/define.go: DefineGlobal@10, DefineIn@36, DefinePattern@47, defineIn@58
  brickmake-rule-semantics-repair/environment/app/internal/expand/expand.go: With@20, New@41, chain@45, Lookup@56, Value@67, plain@83, expandAt@97, appended@109, closing@132, Expand@149, unterminated@193, reference@205, splitArgs@231
  brickmake-rule-semantics-repair/environment/app/internal/expand/expand_test.go: newX@10, TestReferences@18, TestFunctions@37, TestAutomatic@70, TestSelfReference@87
  brickmake-rule-semantics-repair/environment/app/internal/expand/funcs.go: init@23, call@60, eachWord@73, fnSubst@83, fnFindstring@90, filter@97, fnSort@118, number@124, fnWord@133, fnWordlist@145, fnFirstword@164, fnLastword@171, fnSuffix@178, fnAddsuffix@188, fnAddprefix@196, fnJoin@204, fnWildcard@222
  brickmake-rule-semantics-repair/environment/app/internal/parse/cond.go: isConditional@18, skipping@26, conditional@35, evaluate@78, eqArgs@94
  brickmake-rule-semantics-repair/environment/app/internal/parse/lines.go: oddBackslashes@11, hashAt@21, stripComment@31, skipRef@48, findTop@78, splitRecipe@92, scanAssign@111, ScanAssign@140
  brickmake-rule-semantics-repair/environment/app/internal/parse/parse_test.go: read@12, TestRulesAndRecipes@20, TestAssignmentsAndComments@49, TestConditionals@59, TestPatternRulesAndStatic@87, TestTargetAndPatternVars@102
  brickmake-rule-semantics-repair/environment/app/internal/parse/parser.go: New@43, Parse@46, addRecipeLine@79, firstWord@87, statement@96, startsAssignment@122, assign@131, ruleLine@139, targetVar@187
  brickmake-rule-semantics-repair/environment/app/internal/parse/rules.go: flush@20, anyPattern@41, mention@50, recordExplicit@59, recordStatic@70, substAll@96, addRule@104, special@116, defaultGoal@144
  brickmake-rule-semantics-repair/environment/app/internal/text/words.go: isSpace@7, Fields@16, Join@19, TrimSpace@22, TrimLeft@25, IsBlank@28, ParsePattern@37, Match@47, Match@61, Subst@65, Patsubst@74, SplitDir@92, Dir@101, Notdir@110, Suffix@116, Basename@126, SplitOrder@133, Uniq@148
  brickmake-rule-semantics-repair/environment/app/internal/text/words_test.go: TestMatch@5, TestPatsubst@28, TestFileNames@42, TestSplitOrder@57
  brickmake-rule-semantics-repair/environment/app/internal/vars/vars.go: String@17, String@35, NewSet@68, Get@70, Put@77, Len@79, Names@86, String@105, Paste@119
```
</details>

#### 17. No dead/orphaned/unreferenced file under environment/ (basename grep across bundle)
mode: AUTO · status: **FAIL**
- **[MINOR]** `C17-744de9df9d` `brickmake-rule-semantics-repair/environment/.dockerignore` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/.dockerignore
- **[MINOR]** `C17-e46531d760` `brickmake-rule-semantics-repair/environment/app/cmd/brickmake/main.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/cmd/brickmake/main.go
- **[REVIEW]** `C17-c68ecd37bc` `brickmake-rule-semantics-repair/environment/app/docs/functions.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:40) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it
  - evidence: brickmake-rule-semantics-repair/environment/app/docs/functions.md
- **[REVIEW]** `C17-22c9c00cbd` `brickmake-rule-semantics-repair/environment/app/docs/makefiles.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:36) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it
  - evidence: brickmake-rule-semantics-repair/environment/app/docs/makefiles.md
- **[REVIEW]** `C17-3eb6e06ccc` `brickmake-rule-semantics-repair/environment/app/docs/rules.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:38, brickmake-rule-semantics-repair/environment/app/docs/makefiles.md:80, brickmake-rule-semantics-repair/environment/app/docs/updating.md:15) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it
  - evidence: brickmake-rule-semantics-repair/environment/app/docs/rules.md
- **[REVIEW]** `C17-8b4c33ba6b` `brickmake-rule-semantics-repair/environment/app/docs/updating.md` is named only in prose or comments (brickmake-rule-semantics-repair/environment/app/README.md:39, brickmake-rule-semantics-repair/environment/app/docs/variables.md:155) — a mention does not show the file is used; cite the code, build step or contract doc that uses it, or delete it
  - evidence: brickmake-rule-semantics-repair/environment/app/docs/updating.md
- **[MINOR]** `C17-3c34860ff6` `brickmake-rule-semantics-repair/environment/app/examples/demo/src/value.c` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/examples/demo/src/value.c
- **[MINOR]** `C17-59a7c765b4` `brickmake-rule-semantics-repair/environment/app/internal/cli/main.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/cli/main.go
- **[MINOR]** `C17-88492c7c6c` `brickmake-rule-semantics-repair/environment/app/internal/cli/options.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/cli/options.go
- **[MINOR]** `C17-3d3d53ab4e` `brickmake-rule-semantics-repair/environment/app/internal/db/db.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/db/db.go
- **[MINOR]** `C17-809ed76d5f` `brickmake-rule-semantics-repair/environment/app/internal/diag/diag.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/diag/diag.go
- **[MINOR]** `C17-f67c4bac28` `brickmake-rule-semantics-repair/environment/app/internal/engine/deps.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/deps.go
- **[MINOR]** `C17-1137937354` `brickmake-rule-semantics-repair/environment/app/internal/engine/engine.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/engine.go
- **[MINOR]** `C17-d490debfe5` `brickmake-rule-semantics-repair/environment/app/internal/engine/implicit.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/implicit.go
- **[MINOR]** `C17-a7b9218b8a` `brickmake-rule-semantics-repair/environment/app/internal/engine/node.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/node.go
- **[MINOR]** `C17-41b71b7ba0` `brickmake-rule-semantics-repair/environment/app/internal/engine/recipe.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/recipe.go
- **[MINOR]** `C17-19f49b84a4` `brickmake-rule-semantics-repair/environment/app/internal/engine/recipe_test.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/recipe_test.go
- **[MINOR]** `C17-cd77523955` `brickmake-rule-semantics-repair/environment/app/internal/engine/scope.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/scope.go
- **[MINOR]** `C17-73ee51b9e9` `brickmake-rule-semantics-repair/environment/app/internal/engine/update.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/update.go
- **[MINOR]** `C17-a36c67082a` `brickmake-rule-semantics-repair/environment/app/internal/expand/auto.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/auto.go
- **[MINOR]** `C17-94e8181a4b` `brickmake-rule-semantics-repair/environment/app/internal/expand/control.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/control.go
- **[MINOR]** `C17-17ccc8a862` `brickmake-rule-semantics-repair/environment/app/internal/expand/define.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/define.go
- **[MINOR]** `C17-6abf47076f` `brickmake-rule-semantics-repair/environment/app/internal/expand/expand.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/expand.go
- **[MINOR]** `C17-a42b234acf` `brickmake-rule-semantics-repair/environment/app/internal/expand/expand_test.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/expand_test.go
- **[MINOR]** `C17-07a2457caf` `brickmake-rule-semantics-repair/environment/app/internal/expand/funcs.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/funcs.go
- **[MINOR]** `C17-456b6b8a29` `brickmake-rule-semantics-repair/environment/app/internal/parse/cond.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/parse/cond.go
- **[MINOR]** `C17-d222d5d271` `brickmake-rule-semantics-repair/environment/app/internal/parse/lines.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/parse/lines.go
- **[MINOR]** `C17-fdc689590f` `brickmake-rule-semantics-repair/environment/app/internal/parse/parse_test.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/parse/parse_test.go
- **[MINOR]** `C17-7176f2ab65` `brickmake-rule-semantics-repair/environment/app/internal/parse/parser.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/parse/parser.go
- **[MINOR]** `C17-71ce6a1490` `brickmake-rule-semantics-repair/environment/app/internal/parse/rules.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/parse/rules.go
- **[MINOR]** `C17-e7e9c8abb1` `brickmake-rule-semantics-repair/environment/app/internal/text/words.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/text/words.go
- **[MINOR]** `C17-91f82e039e` `brickmake-rule-semantics-repair/environment/app/internal/text/words_test.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/text/words_test.go
- **[MINOR]** `C17-8b054626fa` `brickmake-rule-semantics-repair/environment/app/internal/vars/vars.go` is referenced nowhere else in the bundle
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/vars/vars.go
- note: A file reachable only through a directory COPY + runtime discovery (plugins, data globs) is dismissed with the discovering code cited.

#### 18. No unused helper already implements the core capability (answer-key module)
mode: ASSIST · status: **REVIEW**
- **[REVIEW]** `C18-109c27dd78` unreferenced code module (176 lines, 18 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/cli/main.go
- **[REVIEW]** `C18-474eb77705` unreferenced code module (134 lines, 12 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/cli/options.go
- **[REVIEW]** `C18-8824dc21fb` unreferenced code module (126 lines, 12 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/db/db.go
- **[REVIEW]** `C18-ff990660f7` unreferenced code module (70 lines, 8 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/diag/diag.go
- **[REVIEW]** `C18-50fd087207` unreferenced code module (89 lines, 10 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/deps.go
- **[REVIEW]** `C18-5230b79eda` unreferenced code module (107 lines, 11 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/engine.go
- **[REVIEW]** `C18-0cbf4ea984` unreferenced code module (204 lines, 14 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/implicit.go
- **[REVIEW]** `C18-5d33e17ea0` unreferenced code module (81 lines, 11 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/node.go
- **[REVIEW]** `C18-3ba6c0a436` unreferenced code module (115 lines, 9 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/recipe.go
- **[REVIEW]** `C18-3f3b310df1` unreferenced code module (40 lines, 6 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/recipe_test.go
- **[REVIEW]** `C18-7bd7ee0f90` unreferenced code module (47 lines, 4 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/scope.go
- **[REVIEW]** `C18-542766e8a6` unreferenced code module (184 lines, 16 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/engine/update.go
- **[REVIEW]** `C18-94bbcc27f2` unreferenced code module (80 lines, 4 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/auto.go
- **[REVIEW]** `C18-f7e19bc8cf` unreferenced code module (161 lines, 2 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/control.go
- **[REVIEW]** `C18-4225d36edf` unreferenced code module (73 lines, 4 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/define.go
- **[REVIEW]** `C18-0df139f2e1` unreferenced code module (248 lines, 11 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/expand.go
- **[REVIEW]** `C18-1989e71db5` unreferenced code module (96 lines, 3 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/expand_test.go
- **[REVIEW]** `C18-97605667c5` unreferenced code module (233 lines, 8 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/expand/funcs.go
- **[REVIEW]** `C18-958a5a7662` unreferenced code module (159 lines, 4 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/parse/cond.go
- **[REVIEW]** `C18-8b49e8ff08` unreferenced code module (140 lines, 7 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/parse/lines.go
- **[REVIEW]** `C18-e9797eed88` unreferenced code module (110 lines, 12 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/parse/parse_test.go
- **[REVIEW]** `C18-b208fd6e55` unreferenced code module (200 lines, 9 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/parse/parser.go
- **[REVIEW]** `C18-ccc0cbb742` unreferenced code module (155 lines, 8 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/parse/rules.go
- **[REVIEW]** `C18-d8651f3239` unreferenced code module (158 lines, 7 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/text/words.go
- **[REVIEW]** `C18-8b21d35e0a` unreferenced code module (66 lines, 2 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/text/words_test.go
- **[REVIEW]** `C18-e72e458037` unreferenced code module (127 lines, 6 instruction-vocabulary tokens) — could it be an answer key?
  - evidence: brickmake-rule-semantics-repair/environment/app/internal/vars/vars.go
<details><summary>worksheet (read before answering)</summary>

```
For every hit: remove it, wire it into a legitimate in-fiction caller, or record the decision to keep it as scaffolding (with reason).
```
</details>

#### 19. Docs instruction.md names as authoritative are consistent with instruction.md
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Docs named in instruction.md: /app/docs/cli.md
For each named doc: diff ordering, tie-breaking, numeric formats and edge-case handling against instruction.md sentence by sentence.
```
</details>

#### 20. No un-named environment doc silently holds a rule the tests grade
mode: ASSIST · status: **REVIEW**
- **[REVIEW]** `C20-5ae414d117` brickmake-rule-semantics-repair/environment/app/README.md (not named in instruction.md) contains 4 test literal(s) absent from instruction.md: ['./cmd/brickmake', 'LANG', 'PATH', 'append']
  - evidence: brickmake-rule-semantics-repair/environment/app/README.md
- **[REVIEW]** `C20-c124a30719` brickmake-rule-semantics-repair/environment/app/docs/functions.md (not named in instruction.md) contains 3 test literal(s) absent from instruction.md: ['stderr', 'stdout', 'stem']
  - evidence: brickmake-rule-semantics-repair/environment/app/docs/functions.md
- **[REVIEW]** `C20-38733ed3ef` brickmake-rule-semantics-repair/environment/app/docs/makefiles.md (not named in instruction.md) contains 2 test literal(s) absent from instruction.md: ['PATH', 'append']
  - evidence: brickmake-rule-semantics-repair/environment/app/docs/makefiles.md
- **[REVIEW]** `C20-8feb82a054` brickmake-rule-semantics-repair/environment/app/docs/rules.md (not named in instruction.md) contains 3 test literal(s) absent from instruction.md: ['mention', 'stderr', 'stem']
  - evidence: brickmake-rule-semantics-repair/environment/app/docs/rules.md
- **[REVIEW]** `C20-6a9dfa24c3` brickmake-rule-semantics-repair/environment/app/docs/updating.md (not named in instruction.md) contains 4 test literal(s) absent from instruction.md: ['stderr', 'stdout', 'stem', 'touch']
  - evidence: brickmake-rule-semantics-repair/environment/app/docs/updating.md
- **[REVIEW]** `C20-8533195d17` brickmake-rule-semantics-repair/environment/app/docs/variables.md (not named in instruction.md) contains 3 test literal(s) absent from instruction.md: ['append', 'inherit', 'stem']
  - evidence: brickmake-rule-semantics-repair/environment/app/docs/variables.md

#### 21. Vendored binaries/archives carry no authoring-machine metadata
mode: AUTO · status: **PASS**
- note: scanned 0 binary/archive file(s)

#### 22. Dockerfile never COPY/ADDs solution/ or tests/ (directly or via a parent dir)
mode: AUTO · status: **PASS**
- note: 1 COPY/ADD source(s) read: L26 app/→/app/

#### 23. Any decoy is reachable/inspectable and never labelled as a decoy
mode: ASSIST · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
List every deliberate decoy you know of and, for each, cite the honest path an agent would take to open it (a doc link, an import, a CLI flag).
```
</details>

### SECTION C — SOLUTION/

#### 24. solve.sh diffed file-by-file against environment/ → exact delta list
mode: ASSIST · status: **REVIEW**
- **[REVIEW]** `C24-11237ca001` could not identify any file the solve script writes (unusual form?) — produce the delta by hand
  - evidence: brickmake-rule-semantics-repair/solution/solve.sh
- note: solve script: brickmake-rule-semantics-repair/solution/solve.sh
<details><summary>worksheet (read before answering)</summary>

```
DELTA (container path ← how ← host file; +added/-removed lines vs shipped copy):
Full unified diffs: `python3 scripts/solution_delta.py <task-dir>`. Whole-file replacement is permitted; judge only the delta.
```
</details>

#### 25. Every touched file maps to a real defect/capability instruction.md asks for
mode: MANUAL · status: **MISSING**
<details><summary>worksheet (read before answering)</summary>

```
Fill one line per touched file: <path> → <defect/capability> → <instruction.md line or named doc>
```
</details>

#### 26. No delta changes graded behaviour instruction.md never asks for (scope creep / undisclosed requirement)
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
From the unified diff (check 24), list every hunk that changes behaviour beyond the stated defects. Each is either an undisclosed requirement (fold into check 2) or scope creep to trim.
```
</details>

#### 27. Reference output independently verified CORRECT (not merely test-consistent) — MANDATORY for named math/algorithmic structures
mode: MANUAL · status: **REVIEW**
- note: no sentence asks for a named mathematical/algorithmic structure to be computed — re-derive the reference anyway where its behaviour is non-obvious
<details><summary>worksheet (read before answering)</summary>

```
Required evidence: the independent implementation (or hand derivation) used, the command that ran it on the shipped fixtures, and the diff against solution/'s output. Oracle 3×1.0 is NOT evidence here.
```
</details>

#### 28. If agent trajectories converge on a value ≠ reference, check whether the reference is the outlier
mode: ASSIST · status: **REVIEW**
- **[REVIEW]** `C28-6b35cfb774` `test_outputs.py::test_append_semantics` fails in 3/5 runs with one identical (possibly truncated) message — the message cannot tell the runs apart; a failure count cannot say who is right: compare each run's actual output with instruction.md before calling the reference the outlier
  - evidence: run-03, run-04, run-05: AssertionError: appe...
<details><summary>worksheet (read before answering)</summary>

```
Tests failing in a majority of the 5 runs, grouped by failure message:
  test_outputs.py::test_append_semantics: 3/5
      ['run-03', 'run-04', 'run-05']: AssertionError: appe...
```
</details>

#### 29. solution/ has no orphan files solve.sh does not reference
mode: AUTO · status: **PASS**
- note: every file under solution/ is referenced by solve.sh

#### 30. Per-file ablation: reverting each fixed file alone produces the expected specific test failures
mode: ASSIST · status: **REVIEW**
- note: ablation results loaded from /home/snklp/TERMINAL CHECKER/tb21-final-auditor-main/extracted/ablation-results.json
- note: rebuild before each test run: clean
- note: /app/src/naive.go: reward=0 failed=['test_outputs.py::test_happy_install_status', 'test_outputs.py::test_upgrade_no_mix_clean', 'test_outputs.py::test_crash_install_orphans', 'test_outputs.py::test_crash_upgrade_mixed_version', 'test_outputs.py::test_crash_during_recover_idempotent', 'test_outputs.py::test_rollback_after_crash', 'test_outputs.py::test_conflict_fail_closed', 'test_outputs.py::test_hook_abort_clean', 'test_outputs.py::test_heldout_crash_schedule', 'test_outputs.py::test_remove_clean', 'test_outputs.py::test_usage_exit_4', 'test_outputs.py::test_hook_success_once', 'test_outputs.py::test_rollback_after_upgrade', 'test_outputs.py::test_crash_remove_orphans', 'test_outputs.py::test_crash_during_rollback', 'test_outputs.py::test_recover_noop', 'test_outputs.py::test_duplicate_install_rejected', 'test_outputs.py::test_public_store_schema', 'test_outputs.py::test_hook_crash_at_exec']
- note: script found nothing; a manual PASS with evidence is still required to close this check

#### 31. Oracle builds and runs cleanly from a COLD image build under DOCKER_DEFAULT_PLATFORM=linux/amd64
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Evidence required: the exact command line (with --no-cache / fresh builder), the tail of the build log, and the resulting reward. 'It worked once before' is not evidence.
Helper: `scripts/oracle_build.sh <task-dir>`
```
</details>

### SECTION D — TESTS/

#### 32. Zero individual tests pass under NOP (read nop-1/nop-2 ctrf.json test by test)
mode: AUTO · status: **PASS**
- note: nop-1: 10 tests, statuses={'failed': 10}
- note: nop-2: 10 tests, statuses={'failed': 10}

#### 33. Regression-guard tests are coupled to a real-behaviour assertion in the same function
mode: ASSIST · status: **REVIEW**
- note: no test function is guard-only by heuristic (name or hash/exists-only asserts)
- note: script found nothing; a manual PASS with evidence is still required to close this check
<details><summary>worksheet (read before answering)</summary>

```
For each hit read the whole function. A guard that stands alone is a finding even if today's NOP run happens to fail it.
```
</details>

#### 34. NOP-passable tests are fixed by COUPLING, never by deleting the guard
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Applies only if check 32 or 33 produced findings. Record for each: the coupled assertion added, and that the guard assertion is still present.
```
</details>

#### 35. Every test's assertions read in full and match its name/docstring
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Test inventory — name, docstring first line, #asserts (direct + helpers that assert). Read every body:
  brickmake-rule-semantics-repair/tests/test_outputs.py:50 test_shortest_stem_selection  asserts=0 (+ via replay)  doc=Among matching pattern rules the one with the shortest stem wins, where the
  brickmake-rule-semantics-repair/tests/test_outputs.py:56 test_directory_relative_prerequisites  asserts=0 (+ via replay)  doc=For a slash-less target pattern matched against a name with a directory, the
  brickmake-rule-semantics-repair/tests/test_outputs.py:62 test_mentioned_prerequisite_ought_to_exist  asserts=0 (+ via replay)  doc=A prerequisite that is mentioned anywhere in the makefile counts as one that
  brickmake-rule-semantics-repair/tests/test_outputs.py:68 test_timestamps_reread_after_recipe  asserts=0 (+ via replay)  doc=After a recipe runs the target's time is read again, so a recipe that leaves its
  brickmake-rule-semantics-repair/tests/test_outputs.py:74 test_per_goal_messages  asserts=0 (+ via replay)  doc='Nothing to be done' and 'is up to date' are reported per goal, based only on
  brickmake-rule-semantics-repair/tests/test_outputs.py:80 test_pattern_specific_variable_order  asserts=0 (+ via replay)  doc=Pattern-specific variables from all matching patterns apply from the shortest
  brickmake-rule-semantics-repair/tests/test_outputs.py:86 test_target_variable_inheritance  asserts=0 (+ via replay)  doc=A target's own pattern-specific variables take precedence over the variables it
  brickmake-rule-semantics-repair/tests/test_outputs.py:92 test_append_semantics  asserts=0 (+ via replay)  doc='+=' on a simply expanded variable expands the added text immediately and keeps
  brickmake-rule-semantics-repair/tests/test_outputs.py:98 test_prerequisite_merge_order  asserts=0 (+ via replay)  doc=A target's prerequisites from several rules are combined with the rule that has
  brickmake-rule-semantics-repair/tests/test_outputs.py:104 test_project_builds  asserts=0 (+ via replay)  doc=Multi-step incremental builds of small projects produce the same commands,
```
</details>

#### 36. No test's expected value is computed by agent-editable code
mode: ASSIST · status: **REVIEW**
- note: tests import no module that exists under environment/, add no agent path to sys.path
- note: script found nothing; a manual PASS with evidence is still required to close this check
<details><summary>worksheet (read before answering)</summary>

```
Importing the candidate to OBSERVE its output is fine; importing it to COMPUTE the expected value proves nothing.
```
</details>

#### 37. Test fixtures are not read from an agent-modifiable path that also feeds the expected side
mode: ASSIST · status: **REVIEW**
- note: no absolute data-file path in tests resolves to a shipped environment/ file
- note: script found nothing; a manual PASS with evidence is still required to close this check
<details><summary>worksheet (read before answering)</summary>

```
Safe patterns: fixtures copied from /tests at test time, or expected values hard-coded in the test.
```
</details>

#### 38. Every held-out/hidden scenario genuinely changes the graded outcome vs the public one
mode: ASSIST · status: **REVIEW**
- note: no held-out fixture under tests/ — confirm by reading whether any test varies inputs beyond the shipped fixtures

#### 39. Stated exactness rules are enforced literally (set equality) and the reference satisfies them
mode: ASSIST · status: **REVIEW**
- note: no exactness rule stated in prose
- note: script found nothing; a manual PASS with evidence is still required to close this check
<details><summary>worksheet (read before answering)</summary>

```
No 'exactly these keys / no other fields / unique and sorted' phrasing found in instruction.md or environment docs.
```
</details>

#### 40. Every stated numeric tolerance equals the literal compiled into the assertions
mode: AUTO · status: **PASS**
- note: prose tolerances: -
- note: test tolerances: -

#### 41. No string-obfuscation tricks in tests ("a" + "b" concatenation to defeat grep)
mode: AUTO · status: **PASS**
- note: no literal+literal, ''.join(literals), chr() or decode tricks in tests/

#### 42. No dead/unused test-only code (unused imports, helpers no test calls)
mode: AUTO · status: **PASS**
- note: no unused imports or uncalled helpers in tests/

#### 43. Test names accurately describe what each test checks
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
For every test, compare the name's claim to the body (see check 35 inventory). Rename or fix bodies that diverge.
```
</details>

#### 44. Every fail-closed/rejection test also runs a known-good positive control in the same function
mode: ASSIST · status: **REVIEW**
- note: every rejection-style test also contains a positive assertion
- note: script found nothing; a manual PASS with evidence is still required to close this check

#### 45. Test count in every ctrf.json equals tests collected from the current tests/ tree
mode: AUTO · status: **PASS**
- note: static collection: 10 test(s) from 2 file(s)
- note: oracle-nop-evidence/oracle-1/ctrf.json: 10 tests ✓
- note: oracle-nop-evidence/oracle-2/ctrf.json: 10 tests ✓
- note: oracle-nop-evidence/oracle-3/ctrf.json: 10 tests ✓
- note: oracle-nop-evidence/nop-1/ctrf.json: 10 tests ✓
- note: oracle-nop-evidence/nop-2/ctrf.json: 10 tests ✓
- note: trajectories/run-01/verifier/ctrf.json: 10 tests ✓
- note: trajectories/run-02/verifier/ctrf.json: 10 tests ✓
- note: trajectories/run-03/verifier/ctrf.json: 10 tests ✓
- note: trajectories/run-04/verifier/ctrf.json: 10 tests ✓
- note: trajectories/run-05/verifier/ctrf.json: 10 tests ✓

### SECTION E/F — TASK.TOML + RUBRIC.TXT

#### 46. schema_version = "1.1" is the literal first line of task.toml
mode: AUTO · status: **PASS**
- note: task.toml:1 is `schema_version = "1.1"`

#### 47. description/keywords/[[task.authors]]/category/tags present, accurate, not placeholder/stale
mode: ASSIST · status: **REVIEW**
- note: [[task.authors]] name = "anonymous" ✓ (pool convention — not a placeholder)
<details><summary>worksheet (read before answering)</summary>

```
description: Make a Go GNU-make clone reproduce GNU make 4.3 (-r -R) output for implicit rule search, variable scoping and update decisions
keywords: ['make', 'build-tool', 'go', 'implicit-rules', 'variables']; category: debugging; tags: ['gnu-make', 'pattern-rules', 'target-specific-variables', 'differential-behavior']
description shares 4 content tokens with instruction.md — read both and confirm the description matches the CURRENT defects and fix scope, not an earlier draft.
```
</details>

#### 48. All timeouts (agent/verifier/…) = 7200
mode: AUTO · status: **PASS**
- note: verifier.timeout_sec = 7200.0 ✓
- note: agent.timeout_sec = 7200.0 ✓
- note: environment.build_timeout_sec = 7200.0 ✓

#### 49. No [reference_pattern] or other pipeline/authoring metadata in task.toml
mode: AUTO · status: **PASS**
- note: no reference_pattern / authoring / pipeline / reviewer / qc / audit keys

#### 50. allow_internet = true and no contradicting offline instruction
mode: AUTO · status: **PASS**
- note: environment.allow_internet = true ✓

#### 51. Every rubric line maps to a real test or instruction (nothing grades ungraded behaviour)
mode: ASSIST · status: **REVIEW**
- **[REVIEW]** `C51-d6fd4200f2` rubric.txt:1 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.08)
  - evidence: rubric.txt:1: `Agent reads the relevant sections of /app/docs (rules.md, variables.md, updating.md) before changing engine or expand code, +2`
- **[REVIEW]** `C51-6088340410` rubric.txt:2 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.12)
  - evidence: rubric.txt:2: `Agent reproduces at least one reported symptom with a scratch makefile before editing, +2`
- **[REVIEW]** `C51-9ee4341b94` rubric.txt:3 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.64)
  - evidence: rubric.txt:3: `Agent fixes pattern-rule selection so the stem length includes the directory part of a directory-relative match, +3`
- **[REVIEW]** `C51-70f6aa6786` rubric.txt:4 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_directory_relative_prerequisites, overlap 0.57)
  - evidence: rubric.txt:4: `Agent limits the directory prefix of a directory-relative match to prerequisites that contain '%', +2`
- **[REVIEW]** `C51-7cc9dca218` rubric.txt:5 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_mentioned_prerequisite_ought_to_exist, overlap 0.91)
  - evidence: rubric.txt:5: `Agent treats a prerequisite that is mentioned anywhere in the makefile as one that ought to exist in the first implicit-rule pass, +2`
- **[REVIEW]** `C51-48f6c4480d` rubric.txt:6 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_pattern_specific_variable_order, overlap 0.42)
  - evidence: rubric.txt:6: `Agent orders pattern-specific variables by pattern length and places the file's own pattern set before the inherited parent context, +3`
- **[REVIEW]** `C51-d741a2c52c` rubric.txt:7 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_append_semantics, overlap 0.75)
  - evidence: rubric.txt:7: `Agent makes '+=' on a simply expanded variable expand the added text at once and keeps a target's own '+=' as an in-set append, +3`
- **[REVIEW]** `C51-eec96e2839` rubric.txt:8 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_timestamps_reread_after_recipe, overlap 0.67)
  - evidence: rubric.txt:8: `Agent re-reads a target's time after its recipe runs instead of marking it as newest, +2`
- **[REVIEW]** `C51-d7052cc075` rubric.txt:9 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_per_goal_messages, overlap 0.88)
  - evidence: rubric.txt:9: `Agent reports "up to date" / "Nothing to be done" per goal based only on commands run for that goal, +2`
- **[REVIEW]** `C51-6b667aff6f` rubric.txt:10 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_prerequisite_merge_order, overlap 0.91)
  - evidence: rubric.txt:10: `Agent combines a target's prerequisites from several rules with the recipe rule's list first, then the other rules in makefile order, +2`
- **[REVIEW]** `C51-d664e80151` rubric.txt:11 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_project_builds, overlap 0.40)
  - evidence: rubric.txt:11: `Agent rebuilds brickmake and compares its output against GNU make or the documented examples after the fixes, +3`
- **[REVIEW]** `C51-ea0a52e1b1` rubric.txt:12 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_timestamps_reread_after_recipe, overlap 0.30)
  - evidence: rubric.txt:12: `Agent makes brickmake shell out to or embed GNU make instead of fixing its own logic, -5`
- **[REVIEW]** `C51-541e0d3915` rubric.txt:13 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_directory_relative_prerequisites, overlap 0.12)
  - evidence: rubric.txt:13: `Agent special-cases the file names or flags quoted in the instruction or docs examples, -5`
- **[REVIEW]** `C51-389350aee8` rubric.txt:14 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_shortest_stem_selection, overlap 0.11)
  - evidence: rubric.txt:14: `Agent edits /app/docs to match the existing behavior instead of fixing the code, -3`
- **[REVIEW]** `C51-5e1ebef7f0` rubric.txt:15 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_pattern_specific_variable_order, overlap 0.25)
  - evidence: rubric.txt:15: `Agent changes the command-line interface documented in /app/docs/cli.md, -3`
- **[REVIEW]** `C51-8e74015278` rubric.txt:16 has no [tests: …] tag — name the test that grades it (closest by vocabulary: test_timestamps_reread_after_recipe, overlap 0.12)
  - evidence: rubric.txt:16: `Agent reruns an identical failing command three or more times in a row, -1`
<details><summary>worksheet (read before answering)</summary>

```
rubric line → tagged test (verified to exist) or, untagged, best test / instruction vocabulary overlap:
  L1 UNTAGGED closest test=test_shortest_stem_selection(0.08) instr=0.38  Agent reads the relevant sections of /app/docs (rules.md, variables.md, updating.md) before changing engine or
  L2 UNTAGGED closest test=test_shortest_stem_selection(0.12) instr=0.00  Agent reproduces at least one reported symptom with a scratch makefile before editing, +2
  L3 UNTAGGED closest test=test_shortest_stem_selection(0.64) instr=0.27  Agent fixes pattern-rule selection so the stem length includes the directory part of a directory-relative matc
  L4 UNTAGGED closest test=test_directory_relative_prerequisites(0.57) instr=0.43  Agent limits the directory prefix of a directory-relative match to prerequisites that contain '%', +2
  L5 UNTAGGED closest test=test_mentioned_prerequisite_ought_to_exist(0.91) instr=0.36  Agent treats a prerequisite that is mentioned anywhere in the makefile as one that ought to exist in the first
  L6 UNTAGGED closest test=test_pattern_specific_variable_order(0.42) instr=0.00  Agent orders pattern-specific variables by pattern length and places the file's own pattern set before the inh
  L7 UNTAGGED closest test=test_append_semantics(0.75) instr=0.17  Agent makes '+=' on a simply expanded variable expand the added text at once and keeps a target's own '+=' as 
  L8 UNTAGGED closest test=test_timestamps_reread_after_recipe(0.67) instr=0.11  Agent re-reads a target's time after its recipe runs instead of marking it as newest, +2
  L9 UNTAGGED closest test=test_per_goal_messages(0.88) instr=0.75  Agent reports "up to date" / "Nothing to be done" per goal based only on commands run for that goal, +2
  L10 UNTAGGED closest test=test_prerequisite_merge_order(0.91) instr=0.45  Agent combines a target's prerequisites from several rules with the recipe rule's list first, then the other r
  L11 UNTAGGED closest test=test_project_builds(0.40) instr=0.40  Agent rebuilds brickmake and compares its output against GNU make or the documented examples after the fixes, 
  L12 UNTAGGED closest test=test_timestamps_reread_after_recipe(0.30) instr=0.30  Agent makes brickmake shell out to or embed GNU make instead of fixing its own logic, -5
  L13 UNTAGGED closest test=test_directory_relative_prerequisites(0.12) instr=0.25  Agent special-cases the file names or flags quoted in the instruction or docs examples, -5
  L14 UNTAGGED closest test=test_shortest_stem_selection(0.11) instr=0.44  Agent edits /app/docs to match the existing behavior instead of fixing the code, -3
  L15 UNTAGGED closest test=test_pattern_specific_variable_order(0.25) instr=0.88  Agent changes the command-line interface documented in /app/docs/cli.md, -3
  L16 UNTAGGED closest test=test_timestamps_reread_after_recipe(0.12) instr=0.12  Agent reruns an identical failing command three or more times in a row, -1
A tag proves a test exists, not that it grades the line: read each tagged test and confirm it asserts the behaviour the line describes.
```
</details>

#### 52. Every rubric line is `Agent <does X>, +N` / `, -N`; no headers/blank lines/asides
mode: AUTO · status: **PASS**
- note: 16 lines, all match /^Agent .+, [+-]\d+$/

#### 53. No two rubric lines are mutually unsatisfiable
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Positive vs negative lines sharing vocabulary (read each pair for a contradiction):
  L1: Agent reads the relevant sections of /app/docs (rules.md, variables.md, updating.md) before changing engine or
  L14: Agent edits /app/docs to match the existing behavior instead of fixing the code, -3

  L1: Agent reads the relevant sections of /app/docs (rules.md, variables.md, updating.md) before changing engine or
  L15: Agent changes the command-line interface documented in /app/docs/cli.md, -3

  L11: Agent rebuilds brickmake and compares its output against GNU make or the documented examples after the fixes, 
  L12: Agent makes brickmake shell out to or embed GNU make instead of fixing its own logic, -5

```
</details>

#### 54. No rubric line double-counts the same behaviour under two criteria
mode: ASSIST · status: **REVIEW**
- note: no pair of rubric lines ≥75% similar
- note: script found nothing; a manual PASS with evidence is still required to close this check

#### 55. rubric.txt point budget matches rubric_score.txt MET/NOT MET arithmetic (verify one by hand)
mode: ASSIST · status: **REVIEW**
- note: rubric.txt: 16 scored lines, max positive = 26, total negative = -17
<details><summary>worksheet (read before answering)</summary>

```
trajectories/run-01/rubric_score.txt: 8 verdict lines (rubric has 16); MET-sum=19; stated total=19
trajectories/run-02/rubric_score.txt: 9 verdict lines (rubric has 16); MET-sum=21; stated total=21
trajectories/run-03/rubric_score.txt: 7 verdict lines (rubric has 16); MET-sum=16; stated total=16
trajectories/run-04/rubric_score.txt: 9 verdict lines (rubric has 16); MET-sum=21; stated total=21
trajectories/run-05/rubric_score.txt: 9 verdict lines (rubric has 16); MET-sum=21; stated total=21
Do the arithmetic on at least one file by hand and record it: list each MET line's points, sum, compare with the stated total/gradient.
```
</details>

#### 56. Rubric cites no mechanism/path absent from the shipped environment
mode: AUTO · status: **PASS**
- note: no verifier/tests paths and every cited path resolves or is an output

### SECTION H — ORACLE-NOP-EVIDENCE/

#### 57. oracle-nop-evidence/ is exactly {oracle-1,2,3,nop-1,2}/{ctrf.json,reward.txt,test-stdout.txt}
mode: AUTO · status: **PASS**
- note: structure exact: 5 dirs × 3 files, nothing extra

#### 58. oracle-1/2/3 each reward 1.0 with every test passed (test-by-test)
mode: AUTO · status: **PASS**
- note: oracle-1: reward=1.0, 10 tests, all passed=yes
- note: oracle-2: reward=1.0, 10 tests, all passed=yes
- note: oracle-3: reward=1.0, 10 tests, all passed=yes

#### 59. nop-1/2 each reward 0.0 with every test explicitly 'failed' (not error/skipped)
mode: AUTO · status: **PASS**
- note: nop-1: reward=0.0, 10 tests, all failed=yes
- note: nop-2: reward=0.0, 10 tests, all failed=yes

#### 60. NOP failures are genuine assertion mismatches, not import/crash/infra errors
mode: ASSIST · status: **REVIEW**
- note: nop-1: 87 assertion-looking lines, 0 infra/crash-looking lines
- note: nop-2: 87 assertion-looking lines, 0 infra/crash-looking lines
- note: script found nothing; a manual PASS with evidence is still required to close this check
<details><summary>worksheet (read before answering)</summary>

```
Read both NOP stdout files fully. Only 'shipped code ran and produced the wrong answer' counts as NOP evidence.
```
</details>

#### 61. Evidence mtimes newer than every graded file (tests/, environment/, solution/, instruction.md)
mode: AUTO · status: **PASS**
- note: newest graded file: brickmake-rule-semantics-repair/instruction.md @ 2026-09-26 19:42:08

#### 62. Duplication check on the evidence set (3 independent oracle passes, 2 independent NOP fails)
mode: AUTO · status: **PASS**
- note: oracle-1: start=1790432267.1314867 stop=1790432267.7008305 ctrf=f1cc78af84ae stdout=1a2df9e6ac2c
- note: oracle-2: start=1790432321.7859943 stop=1790432322.3372068 ctrf=a30d88bf620d stdout=6575e59eb295
- note: oracle-3: start=1790434756.4598238 stop=1790434757.060153 ctrf=c740482c071a stdout=70ab9bc8f2ca
- note: nop-1: start=1790432426.8692417 stop=1790432427.4747438 ctrf=fa4f4a729e40 stdout=4a551ac12236
- note: nop-2: start=1790432487.2147746 stop=1790432487.8182902 ctrf=c9c56d49c687 stdout=24760de1e039

### SECTION G — TRAJECTORIES/

#### 63. SUMMARY.txt is exactly 2 lines: slug+sha+model+reasoning_effort, then the 5-run reward array
mode: AUTO · status: **PASS**
- note: L1: brickmake-rule-semantics-repair sha=0babf476219b8958 model=@openai/gpt-5.6 reasoning_effort=xhigh k=5 | L2: [0, 1, 0, 0, 0]

#### 64. Every rubric_score.txt is pure data + evidence citations (no note:/Summary:/process narration)
mode: AUTO · status: **PASS**
- note: 5 rubric_score.txt files free of note:/Summary:/session narration

#### 65. SUMMARY.txt reward array == each run's verifier/reward.txt == its ctrf.json outcome, in order
mode: AUTO · status: **PASS**
- note: run-01: SUMMARY=0.0 reward.txt=0.0 ctrf=9/10
- note: run-02: SUMMARY=1.0 reward.txt=1.0 ctrf=10/10
- note: run-03: SUMMARY=0.0 reward.txt=0.0 ctrf=7/10
- note: run-04: SUMMARY=0.0 reward.txt=0.0 ctrf=9/10
- note: run-05: SUMMARY=0.0 reward.txt=0.0 ctrf=9/10

#### 66. SUMMARY.txt bundle sha == fresh recompute from disk (find|sort|shasum pipeline)
mode: AUTO · status: **PASS**
- note: recomputed sha (shell) from inside inner brickmake-rule-semantics-repair/: 0babf476219b8958; SUMMARY.txt sha: 0babf476219b8958

#### 67. Newest graded mtime is OLDER than every trajectories/run-*/ and every evidence ctrf.json
mode: AUTO · status: **PASS**
- note: newest graded file: brickmake-rule-semantics-repair/instruction.md @ 2026-09-26 19:42:08

#### 68. oracle-1/2/3 are three independent executions (timestamps, addresses, hashes differ)
mode: AUTO · status: **PASS**
- note: oracle-1: start=1790432267.1314867 stop=1790432267.7008305 ctrf=f1cc78af84ae stdout=1a2df9e6ac2c
- note: oracle-2: start=1790432321.7859943 stop=1790432322.3372068 ctrf=a30d88bf620d stdout=6575e59eb295
- note: oracle-3: start=1790434756.4598238 stop=1790434757.060153 ctrf=c740482c071a stdout=70ab9bc8f2ca

#### 69. nop-1/2 are two independent executions
mode: AUTO · status: **PASS**
- note: nop-1: start=1790432426.8692417 stop=1790432427.4747438 ctrf=fa4f4a729e40 stdout=4a551ac12236
- note: nop-2: start=1790432487.2147746 stop=1790432487.8182902 ctrf=c9c56d49c687 stdout=24760de1e039

#### 70. For every failing run the real failure was read from trajectory.json + test-stdout.txt and matches rubric_score.txt's claim
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
run-01: reward=0.0 failing=['test_outputs.py::test_mentioned_prerequisite_ought_to_exist']
    stdout first error: E       AssertionError: mention/prerequisite_mentioned_elsewhere_ought_to_exist result #1
    rubric_score first NOT MET: Agent reproduces at least one reported symptom with a scratch makefile before editing | NOT MET | 0 | First source edit `// GNU make applies less specific (shor
run-03: reward=0.0 failing=['test_outputs.py::test_shortest_stem_selection', 'test_outputs.py::test_mentioned_prerequisite_ought_to_exist', 'test_outputs.py::test_append_semantics']
    stdout first error: E       AssertionError: stem/shortest_stem_wins_across_directories result #0
    rubric_score first NOT MET: Agent reproduces at least one reported symptom with a scratch makefile before editing | NOT MET | 0 | the first scratch makefile run came only after the update.
run-04: reward=0.0 failing=['test_outputs.py::test_append_semantics']
    stdout first error: E       AssertionError: append/simple_variables_expand_appended_text_now result #0
    rubric_score first NOT MET: Agent reproduces at least one reported symptom with a scratch makefile before editing | NOT MET | 0 | The first Go edit ending in `gofmt -w internal/engine/engi
run-05: reward=0.0 failing=['test_outputs.py::test_append_semantics']
    stdout first error: E       AssertionError: append/simple_variables_expand_appended_text_now result #0
    rubric_score first NOT MET: Agent reproduces at least one reported symptom with a scratch makefile before editing | NOT MET | 0 | the first refresh edit was attempted before any scratch ru
For each failing run, quote the trajectory step where the agent went wrong and the stdout assertion, and confirm rubric_score.txt names the same cause.
```
</details>

#### 71. The 5 rubric_score.txt files are not byte-identical / near-identical copies
mode: AUTO · status: **PASS**
- note: trajectories/run-01/rubric_score.txt vs trajectories/run-02/rubric_score.txt: similarity 0.37 after removing run numbers and timings
- note: trajectories/run-01/rubric_score.txt vs trajectories/run-03/rubric_score.txt: similarity 0.36 after removing run numbers and timings
- note: trajectories/run-01/rubric_score.txt vs trajectories/run-04/rubric_score.txt: similarity 0.35 after removing run numbers and timings
- note: trajectories/run-01/rubric_score.txt vs trajectories/run-05/rubric_score.txt: similarity 0.28 after removing run numbers and timings
- note: trajectories/run-02/rubric_score.txt vs trajectories/run-03/rubric_score.txt: similarity 0.35 after removing run numbers and timings
- note: trajectories/run-02/rubric_score.txt vs trajectories/run-04/rubric_score.txt: similarity 0.49 after removing run numbers and timings
- note: trajectories/run-02/rubric_score.txt vs trajectories/run-05/rubric_score.txt: similarity 0.38 after removing run numbers and timings
- note: trajectories/run-03/rubric_score.txt vs trajectories/run-04/rubric_score.txt: similarity 0.18 after removing run numbers and timings
- note: trajectories/run-03/rubric_score.txt vs trajectories/run-05/rubric_score.txt: similarity 0.17 after removing run numbers and timings
- note: trajectories/run-04/rubric_score.txt vs trajectories/run-05/rubric_score.txt: similarity 0.43 after removing run numbers and timings

#### 72. Every NOT MET / negative verdict cites a line, function or quoted value found in THAT run's own trajectory/stdout
mode: ASSIST · status: **FAIL**
- **[MAJOR]** `C72-4301f1500b` run-01: citation ['TestPatternCannotChangeCommandLineVariable', 'cli.md'] is a bare word — it does not substantiate this verdict; cite the failing assertion, a step number or a quoted multi-word output
  - evidence: trajectories/run-01/rubric_score.txt:15: `Agent changes the command-line interface documented in /app/docs/cli.md | NOT MET | 0 | No internal/cli edit; extra work was an expand test `TestPatternCannotCh…`
<details><summary>worksheet (read before answering)</summary>

```
A specific citation is necessary, not sufficient: read the cited spot and confirm it supports the verdict.
```
</details>

#### 73. MET verdicts spot-checked against the run's own trajectory (no over-claimed MET)
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
trajectories/run-01/rubric_score.txt: 8 MET lines
trajectories/run-02/rubric_score.txt: 9 MET lines
trajectories/run-03/rubric_score.txt: 7 MET lines
trajectories/run-04/rubric_score.txt: 9 MET lines
trajectories/run-05/rubric_score.txt: 9 MET lines
Pick at least the passing runs; for each MET line, cite the trajectory step proving the agent actually did it.
```
</details>

#### 74. PII scrub clean across every trajectory file (/Users/, /private/tmp/, /home/<user>, \bstb\b)
mode: AUTO · status: **PASS**
- note: 50 trajectory files scanned; zero host-path or \bstb\b hits

#### 75. config.json trials_dir / task.path / trial_uri scrubbed to /terminal-bench2.1/<slug> form
mode: AUTO · status: **PASS**
- note: all path-like config fields use /terminal-bench2.1/brickmake-rule-semantics-repair

#### 76. result.json model fields left at raw captured form (not hand-edited to match config.json)
mode: AUTO · status: **PASS**
- note: run-01: config.agent.model_name='openai/@openai/gpt-5.6' agent_info.model_info.name='@openai/gpt-5.6'
- note: run-02: config.agent.model_name='openai/@openai/gpt-5.6' agent_info.model_info.name='@openai/gpt-5.6'
- note: run-03: config.agent.model_name='openai/@openai/gpt-5.6' agent_info.model_info.name='@openai/gpt-5.6'
- note: run-04: config.agent.model_name='openai/@openai/gpt-5.6' agent_info.model_info.name='@openai/gpt-5.6'
- note: run-05: config.agent.model_name='openai/@openai/gpt-5.6' agent_info.model_info.name='@openai/gpt-5.6'

#### 77. Every agent/ folder has the same canonical file set (api-calls.jsonl, recording.cast, *.pane, trajectory.json)
mode: AUTO · status: **PASS**
- note: all 5 runs: ['*.pane', 'api-calls.jsonl', 'recording.cast', 'trajectory.json']

#### 78. Every verifier/ has ctrf.json, reward.txt, test-stdout.txt; reward.txt matches ctrf outcome
mode: AUTO · status: **PASS**
- note: run-01: reward=0.0, ctrf 9/10 ✓
- note: run-02: reward=1.0, ctrf 10/10 ✓
- note: run-03: reward=0.0, ctrf 7/10 ✓
- note: run-04: reward=0.0, ctrf 9/10 ✓
- note: run-05: reward=0.0, ctrf 9/10 ✓

#### 79. reasoning_effort == "xhigh" on every one of the 5 runs individually
mode: AUTO · status: **PASS**
- note: run-01: xhigh ✓
- note: run-02: xhigh ✓
- note: run-03: xhigh ✓
- note: run-04: xhigh ✓
- note: run-05: xhigh ✓

#### 80. No run's result.json has exception_info populated (infra error invalidates the reward)
mode: AUTO · status: **PASS**
- note: run-01: exception_info empty ✓
- note: run-02: exception_info empty ✓
- note: run-03: exception_info empty ✓
- note: run-04: exception_info empty ✓
- note: run-05: exception_info empty ✓

#### 81. Reward-hacking scan per trajectory: no /tests, test_outputs.py, ctrf/reward, /opt/verifier, solution/ access; no hand-written outputs; no truncation; genuine completion
mode: ASSIST · status: **REVIEW**
- note: no graded-path access, truncation markers or shell-written outputs in any transcript
- note: script found nothing; a manual PASS with evidence is still required to close this check
<details><summary>worksheet (read before answering)</summary>

```
run-01: 31 steps; last step: {"step_id": 31, "timestamp": "2026-09-26T14:28:08.919198+00:00", "source": "agent", "model_name": "gpt-5.6-sol", "message": "Analysis: Yes. The required behavioral fixes are implemented. Focused reproductions pass, and final validation succeeded with `go test -count=1 ./...`, `go vet ./...`, and a p
run-02: 36 steps; last step: {"step_id": 36, "timestamp": "2026-09-26T14:29:07.386641+00:00", "source": "agent", "model_name": "gpt-5.6-sol", "message": "Analysis: Yes. The fixes compile cleanly and have been validated with the full test suite, `go vet`, and targeted black-box scenarios covering every reported discrepancy.\nPla
run-03: 34 steps; last step: {"step_id": 34, "timestamp": "2026-09-26T14:45:41.900571+00:00", "source": "agent", "model_name": "gpt-5.6-sol", "message": "Analysis: Yes. All identified behavioral mismatches were fixed and verified with focused integration scenarios. The final formatting, uncached test suite, vet checks, and requ
run-04: 47 steps; last step: {"step_id": 47, "timestamp": "2026-09-26T14:48:19.089512+00:00", "source": "agent", "model_name": "gpt-5.6-sol", "message": "Analysis: Yes. The implementation is complete and verified: all reported scenarios produce the specified behavior, regression tests cover the core fixes, `go test -count=1 ./.
run-05: 40 steps; last step: {"step_id": 40, "timestamp": "2026-09-26T14:48:36.358484+00:00", "source": "agent", "model_name": "gpt-5.6-sol", "message": "Analysis: The implementation changes are complete and validated. `go vet ./...`, `go test -count=1 ./...`, and a plain build of `/app/cmd/brickmake` all succeed. Focused integ
```
</details>

#### 82. After any k=5 rerun the six artefacts moved together (5 run dirs, SUMMARY, 5 rubric_scores, task.toml estimates, sha, fresh PII grep)
mode: AUTO · status: **PASS**
- note: run dirs span 2026-09-26 20:27:10 → 2026-09-26 20:29:08
<details><summary>worksheet (read before answering)</summary>

```
Item (6): the PII/stb/reference_pattern grep must be re-run after the rerun — check 85 covers it and must be the literal last step.
```
</details>

### SECTION I — CROSS-ARTIFACT / STRUCTURAL

#### 83. No manufactured difficulty — classify the difficulty SOURCE (reasoning/engineering vs obscurity, transcription, decoys, hidden rules, compliance walls)
mode: MANUAL · status: **REVIEW**
<details><summary>worksheet (read before answering)</summary>

```
Classify explicitly, with one sentence of justification each: (a) what makes the task hard, (b) which of {diagnosis, multi-step inference, edge-case/fault/state handling} it exercises, (c) whether any difficulty comes from obscurity (check 15), spec transcription (check 3/10), unfair decoys (23), hidden/contradictory requirements (2/9/20) or compliance walls (5).
k=5 rewards for context: [0.0, 1.0, 0.0, 0.0, 0.0]
```
</details>

#### 84. Delivery structure exact: <slug>/{ <slug>/{instruction.md,task.toml,environment,solution,tests}, rubric.txt, oracle-nop-evidence/, trajectories/ } — nothing else, no junk, no extra wrapper
mode: AUTO · status: **PASS**
- note: brickmake-rule-semantics-repair/ = { brickmake-rule-semantics-repair/{5 core items}, rubric.txt, oracle-nop-evidence/, trajectories/{run-01..05, SUMMARY.txt} }; no junk
- note: layout detected: nested; outer=/home/snklp/TERMINAL CHECKER/tb21-final-auditor-main/extracted/brickmake-rule-semantics-repair; inner=/home/snklp/TERMINAL CHECKER/tb21-final-auditor-main/extracted/brickmake-rule-semantics-repair/brickmake-rule-semantics-repair

#### 85. FINAL post-every-edit grep for \bstb\b, /Users/, /private/tmp/, /home/<user> across the ENTIRE bundle (last step before zipping)
mode: AUTO · status: **PASS**
- note: 115 files scanned across the whole bundle; zero hits
<details><summary>worksheet (read before answering)</summary>

```
This must be re-run as the literal last step before zipping (scripts/final_scrub.sh). Also grep reference_pattern (check 49).
```
</details>
