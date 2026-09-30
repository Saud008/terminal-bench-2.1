# Master Ship Checklist - zonefile-master-repair

Bundle sha `ee9eb7b8a0507398`, generated 2026-09-27 11:47. FAIL 0, STALE 0, REVIEW 0, MANUAL 0, SIGNED 42, PASS 45

| # | Sec | Check | Mode | Status | First finding |
|---|---|---|---|---|---|
| CI | - | CI / pool static gates (pinned deps, base image, test.sh, docstrings, ruff, diversity) | auto | **SIGNED** | [diversity] 0/5 solved = CHALLENGE — needs a written justification that the failure is real capability |
| 0 | A | Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens | assist | **SIGNED** |  |
| 1 | A | Every stated requirement is exercised by a test | assist | **SIGNED** |  |
| 2 | A | Every requirement a test enforces is stated | assist | **SIGNED** |  |
| 3 | A | No implementation-step ('how') sentences | assist | **SIGNED** |  |
| 4 | A | Interface contracts named in the prompt are really graded | manual | **SIGNED** |  |
| 5 | A | No grader / test-suite / pipeline terms | auto | **PASS** |  |
| 6 | A | Stated constants match tests byte for byte | assist | **SIGNED** |  |
| 7 | A | Every path the prompt names exists in the built image | auto | **PASS** |  |
| 8 | A | Output schema exactness in prose matches the tests | assist | **SIGNED** | instruction.md:9 exactness rule "The docs in `/app/docs` are the spec for what zonec accepts, how defaults are filled in |
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
| 31 | C | Cold linux/amd64 oracle build runs cleanly | auto | **PASS** | cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-27T11:44:12 (baselines.json) |
| 32 | D | Zero individual tests pass under NOP | auto | **PASS** |  |
| 33 | D | Guard-style tests are coupled to real behavior | assist | **SIGNED** |  |
| 34 | D | NOP-passable guards coupled, not deleted | manual | **SIGNED** |  |
| 35 | D | Assertions do what names/docstrings claim | assist | **SIGNED** |  |
| 36 | D | Expected values never computed by agent-editable code | assist | **SIGNED** |  |
| 37 | D | Fixtures feeding expected values are not agent-editable | assist | **SIGNED** |  |
| 38 | D | Held-out scenarios really change the graded outcome | manual | **SIGNED** |  |
| 39 | D | Exactness rules enforced literally (set equality) | assist | **SIGNED** | instruction.md:9 "The docs in `/app/docs` are the spec for what zonec accepts, how defaults are filled in, and what the  |
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
| 51 | F | Every rubric line maps to a test or instruction | assist | **SIGNED** | rubric line "Agent adds the second SHA-384 padding block when fewer than 16 bytes remain for the 128-bit length" maps to |
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

### CI - CI / pool static gates (pinned deps, base image, test.sh, docstrings, ruff, diversity) [SIGNED]
- warn: [diversity] 0/5 solved = CHALLENGE — needs a written justification that the failure is real capability
- sign-off (pass): Pool CI gates clean (tb21_check.py: `0 error(s), 0 warning(s)`). The remaining diversity note is the 0/5 CHALLENGE result; written justification is signed under check 83 (SHA-384 second-padding-block boundary missed in all 5 runs despite hashlib cross-checks on small zones; \DDD folding rule in master-files.md:85-87 missed in 4 runs). difficulty = "hard" in task.toml:17, consistent with the tickwheel precedent for 0/5.

### 0 - Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens [SIGNED]
- sign-off (pass): instruction.md is 11 lines of plain prose written for this task (symptom list lines 3-7, scope line 9, constraints line 11); every absolute path is in backticks: `/app` (l1), `/app/docs` and `/app/examples` (l9), `/app/docs/zonec.1.md` (l11). The output is named: the canonical listing on stdout per `/app/docs/zonec.1.md` (l11) and docs/output.md. ~300 tokens, far below 1500.

### 1 - Every stated requirement is exercised by a test [SIGNED]
- sign-off (pass): Each stated symptom maps to a test group: $ORIGIN owner (instruction.md:3) -> test_owner_continuation tests/test_outputs.py:107; relative $INCLUDE from another cwd (l4) -> test_include_paths :122, run with cwd=elsewhere at :72-79; `"ok :-)"` (l5) -> test_quoted_parentheses :127; canonical order / apex first (l6) -> test_canonical_order :142; ZONEMD digest (l7) -> test_zonemd :152. Constraints of l11: C library only -> FORBIDDEN_CALLS :22-25 + _source_policy_problems :42; CLI/exit codes/diagnostics -> _check_group :90-103 checks exit 0/1, empty stdout and `FILE:LINE: ` prefix; `make` with `BUILD=` -> fixture :60-66 builds with BUILD=/tmp/zonec-verify-build.

### 2 - Every requirement a test enforces is stated [SIGNED]
- sign-off (pass): Every graded behavior is a documented rule the instruction points to (instruction.md:9 `The docs in /app/docs are the spec`): default TTL order master-files.md:53-63 (test_default_ttl); $INCLUDE state revert master-files.md:68-76 (test_include_scope); relative include path master-files.md:67 (test_include_paths); quoted parentheses master-files.md:14-16 (test_quoted_parentheses); \DDD decoded then folded master-files.md:81-87 (test_escaped_case, test_escaped_label_length: `A label holds 1 to 63 octets` l83); RRset TTL output.md:38-42 (test_rrset_ttl); canonical order output.md:46-55 (test_canonical_order); ZONEMD apex/serial/digest zonemd.md:15-45 (test_zonemd); error format zonec.1.md:16-35 (error cases). The source-policy grep enforces instruction.md:11 `no running other programs`.

### 3 - No implementation-step ('how') sentences [SIGNED]
- sign-off (pass): No sentence says how to fix anything: instruction.md:3-7 are observed symptoms, l9 says follow the docs, l11 lists constraints (language, CLI, make). No file, function or algorithm to change is named.

### 4 - Interface contracts named in the prompt are really graded [SIGNED]
- sign-off (pass): Contracts named: command line/exit codes/diagnostic format of `/app/docs/zonec.1.md` (instruction.md:11) are graded by tests/test_outputs.py:78 (`zonec -o ORIGIN FILE`), :91 (exit 0 + exact stdout) and :97-99 (exit 1, empty stdout, stderr starting `FILE:LINE: `); `make ... BUILD=` graded at :60-66; plain C library graded at :22-25/:42-51.

### 6 - Stated constants match tests byte for byte [SIGNED]
- sign-off (pass): The instruction states no numeric constants. The only literal is the TXT example `smile IN TXT "ok :-)"` (instruction.md:5); tests/cases.json quoted_parentheses group contains the same `"ok :-)"` style strings, and docs constants (63 octets master-files.md:83, 8 include levels l77, SHA-384 zonemd.md:17) match the generated cases (escaped_label_length accepts 63 and rejects 64 decoded octets).

### 8 - Output schema exactness in prose matches the tests [SIGNED]
- warn: instruction.md:9 exactness rule "The docs in `/app/docs` are the spec for what zonec accepts, how defaults are filled in, and what the listing looks like" but tests/ show no set/list equality assertion
- sign-off (pass): The exactness rule (instruction.md:9 `make zonec follow them exactly`) is enforced as whole-string equality of stdout: tests/test_outputs.py:91 `(proc.returncode, proc.stdout) != (0, case["stdout"])` compares the full listing byte for byte, which is stricter than set equality and matches output.md:13 `Nothing else is printed`. The heuristic only missed it because the comparison is a tuple inequality, not assert ==.

### 9 - No self-contradiction between sentences [SIGNED]
- sign-off (pass): Read instruction.md l1-11 and docs: no two sentences conflict. l9 `also where they pick a different behavior than BIND` is consistent with master-files.md:4-6 `Where other implementations disagree ... the rule written here is the one zonec follows` and output.md:38-40 (first-record TTL, which differs from BIND's handling).

### 10 - Prompt does not narrate each planted defect's mechanism [SIGNED]
- sign-off (pass): instruction.md:3-7 describe what users saw (wrong owner, cwd-dependent include, rejected TXT, wrong order, rejected digest), never the mechanism: no mention of strchr/strrchr, has_last/has_dollar, fold(), label text length, strcmp, TTL min, digest call order, type==ZONEMD, SHA padding. 8 of 13 defects (TTL precedence, include TTL scope, \DDD fold, label length, RRset TTL, apex-only exclusion, serial source, padding bound) are not mentioned at all.

### 11 - Every environment file is required [SIGNED]
- sign-off (pass): All 43 environment files are used: Dockerfile/.dockerignore build the image; Makefile builds every src/*.c (wildcard) and is graded by the BUILD= build; the 5 docs are the spec (instruction.md:9); README.md is the project map the docs index; the 3 examples files (example.net.zone includes office/hosts.inc; reverse zone) are the sample zones the instruction names (`/app/examples`, l9) and that README.md:13 runs. Every src file is linked into zonec (ablation appendix: removing any fixed file breaks tests).

### 13 - No comments echoing instruction or rubric text [SIGNED]
- sign-off (pass): Only 6 comments in src/*.c: sha384.c:117 (length field width), zone.c:55 (states RFC 4034 order contract), rr_zonemd.c:19 (token grammar), directives.c:7 (include path contract), rr_names.c:3, rr_addr.c:55 (RFC 5952 form). They are ordinary API/contract comments using RFC terms; none copies an instruction sentence (instruction.md:3-7) or a rubric line wording, and none marks a defect.

### 14 - No lore/notes doc indexing the planted defects [SIGNED]
- sign-off (pass): No notes/TODO/CHANGELOG file exists (environment file list: Makefile, README.md, docs/*.md x5, examples x3, src x32). README.md:23-31 maps files to areas (`src/zone.c - record store, duplicates, RRset TTLs, ordering, output`) but lists no defects; docs describe intended behavior only.

### 16 - No names that mislabel behavior [SIGNED]
- sign-off (pass): Names match intended behavior: `ttl_ctx_default` (src/ttl.c:65) picks the default TTL, `do_origin` / `do_include` / `include_path` (src/directives.c:27, :50, :9) handle $ORIGIN, $INCLUDE and include path joining, `rr_cmp` (src/zone.c:57) is the record comparator, `zonemd_update` (src/zonemd.c:28) fills the apex ZONEMD, `sha384_final` (src/sha384.c:107) finishes the hash, `name_parse` (src/name.c:18) parses names. The defects sit inside these correctly named functions; no identifier claims a behavior the code is not meant to have.

### 18 - No unused module that already implements the answer [SIGNED]
- sign-off (pass): No unused module implements the answer: every .c is compiled and linked (Makefile wildcard), there is no second name comparator or alternative lexer; the RFC 4034 comparison had to be written in zone.c rr_cmp by the solution (solve.sh:561-674).

### 19 - Authoritative docs consistent with instruction.md [SIGNED]
- sign-off (pass): Docs agree with instruction.md: owner after $ORIGIN (instruction l3) vs master-files.md:42-44; include paths (l4) vs master-files.md:67-68 and zonec.1.md:29-31; quoted parentheses (l5) vs master-files.md:14-16; canonical order, apex first (l6) vs output.md:46-52 `a name sorts before every name below it`; ZONEMD (l7) vs zonemd.md. CLI/exit codes (l11) vs zonec.1.md:3-35.

### 20 - Non-authoritative docs hold no hidden graded rule [SIGNED]
- sign-off (pass): All five docs are authoritative per instruction.md:9 (`The docs in /app/docs are the spec`). README.md (non-authoritative) states only build commands and file layout (README.md:11-31), which are either graded consistently (make BUILD=) or not graded; it holds no hidden rule.

### 23 - Decoys are reachable, fair and not labelled [SIGNED]
- sign-off (pass): There are no planted decoys. The only non-graded material is /app/examples (sample zones, reachable via README.md:13) and README.md's per-file map; neither is labelled as a hint or trap. Only real defects are graded; no decoy is scored against the agent (tests only compare generated case listings).

### 24 - solve.sh delta listed file by file [SIGNED]
- sign-off (pass): Solution delta appendix: solve.sh rewrites 7 files via heredoc: lexer.c (solve.sh:7-174, +9/-9: quoted parens), name.c (:177-379, +17/-11: \DDD fold + octet label length), ttl.c (:382-459, +4/-4: $TTL before last TTL), directives.c (:462-558, +3/-3: $ORIGIN owner, include TTL save/restore, strrchr), zone.c (:561-674, +7/-8: canonical rr_cmp, first-record RRset TTL, digest after TTLs), zonemd.c (:677-735, +2/-2: apex-only exclusion, SOA serial), sha384.c (:738-863, +1/-1: >112 padding bound). Then `make`.

### 25 - Every touched file maps to a requested fix (no no-op delta) [SIGNED]
- sign-off (pass): Solution delta appendix in _reports/zonefile-master-repair/MASTER_REPORT.md lists 7 heredocs in solution/solve.sh (lexer.c solve.sh:7-174, name.c :177-379, ttl.c :382-459, directives.c :462-558, zone.c :561-674, zonemd.c :677-735, sha384.c :738-863), each with a non-zero diff. The ablation in _reports/zonefile-master-repair/ablation.json shows every one of them alone drops the reward to 0 (e.g. `/app/src/sha384.c` removed -> failing test_zonemd; `/app/src/lexer.c` removed -> test_quoted_parentheses, test_reference_zone). No no-op file.

### 26 - No out-of-scope delta [SIGNED]
- sign-off (pass): The delta is limited to the 13 documented behaviors (diff sizes above, max +17/-11 in name.c); no CLI, diagnostic wording, Makefile, docs or test changes (`_reports/zonefile-master-repair/authoring/fix.diff` touches only src/{lexer,name,ttl,directives,zone,zonemd,sha384}.c).

### 27 - Reference output independently re-derived [SIGNED]
- sign-off (pass): tests/cases.json listings were re-derived independently: `_reports/zonefile-master-repair/authoring/crosscheck.py` (dnspython 2.7) matched every success listing except the documented first-record-vs-minimum RRset TTL divergence (output.md:38-42), and every ZONEMD digest was recomputed with dnspython `dns.zone.Zone.compute_digest` (SHA-384, SIMPLE) and matched; `bindcheck.py` (BIND 9.18 named-compilezone) matched the record multisets. Stated in tests/test_outputs.py:1-6.

### 28 - Agent consensus vs reference outlier checked [SIGNED]
- sign-off (pass): Agent consensus vs reference: all 5 runs (trajectories/run-01..05/verifier/test-stdout.txt) fail only `zonemd/digest_input_near_block_end` in test_zonemd; four fail `escaped_case/decimal_escapes_fold_case`. The reference for both was re-derived independently: `docker run ... python:3.12-slim ... crosscheck.py tests/cases.json` (dnspython 2.7.0) printed `zonemd ok: zonec 880977E80C2B78B3.. dnspython 880977E80C2B78B3.. serial 2026092706 vs SOA 2026092706` for the near-block-end case; \DDD folding follows master-files.md:85-87 `octets A to Z become a to z, however they were written`, which dnspython also applies (names compare case-insensitively). The agents are the outlier, not the reference: none of them edited src/sha384.c and four left name.c folding untouched.

### 30 - Each fix ablated alone produces test failures [PASS]

### 31 - Cold linux/amd64 oracle build runs cleanly [PASS]
- info: cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-27T11:44:12 (baselines.json)

### 33 - Guard-style tests are coupled to real behavior [SIGNED]
- sign-off (pass): The only guard-style checks are in the session fixture (tests/test_outputs.py:54-67): source policy and build. They cannot pass on their own: every test also runs _check_group (:85-104) comparing real zonec output. NOP fails 11/11 on behavior (oracle-nop-evidence/nop-1/ctrf.json).

### 34 - NOP-passable guards coupled, not deleted [SIGNED]
- sign-off (n/a): No test passes under NOP: oracle-nop-evidence/nop-1/ctrf.json and nop-2/ctrf.json summaries read `"tests": 11, "passed": 0, "failed": 11` (checked with py -3 reading results.summary), so there is no NOP-passable guard to couple.

### 35 - Assertions do what names/docstrings claim [SIGNED]
- sign-off (pass): Each test is a one-line call to _check_group on the group its name and docstring describe (tests/test_outputs.py:107-158), and the groups in tests/cases.json contain exactly those scenarios (e.g. zonemd group: apex digest, non-apex ZONEMD as data, SHA-512 apex rejected, matching the docstring at :153).

### 36 - Expected values never computed by agent-editable code [SIGNED]
- sign-off (pass): Expected values come only from tests/cases.json (loaded at tests/test_outputs.py:20), generated offline from the reference build and cross-checked; tests never call /app code to compute expectations, the build goes to /tmp/zonec-verify-build (:19, :61) and is only the system under test.

### 37 - Fixtures feeding expected values are not agent-editable [SIGNED]
- sign-off (pass): tests/cases.json lives in tests/, which is copied in only at verification time and is not under /app; the Dockerfile copies only environment/app (check 22 PASS). Case files are written to fresh mkdtemp dirs (:71-76).

### 38 - Held-out scenarios really change the graded outcome [SIGNED]
- sign-off (pass): Held-out cases differ from /app/examples (instruction.md:9 `It will be run on zone files other than the ones in /app/examples`): cases.json zones use other names/origins and change the outcome; ablation shows each group flips on its defect (ablation appendix).

### 39 - Exactness rules enforced literally (set equality) [SIGNED]
- warn: instruction.md:9 "The docs in `/app/docs` are the spec for what zonec accepts, how defaults are filled in, and what the listing looks like" - no literal equality enforcement found in tests/
- sign-off (pass): Same as check 8: exactness is enforced literally by full-string equality of stdout at tests/test_outputs.py:91 and exit-code equality; error cases check exit 1, stdout == "" and the exact `FILE:LINE: ` prefix (:97-99), which is the whole documented interface (zonec.1.md:36 `The wording of the message is not part of the interface`).

### 40 - Test tolerances equal the stated tolerances [SIGNED]
- sign-off (n/a): No numeric tolerance is stated or used; all comparisons are exact (tests/test_outputs.py:91, :99).

### 43 - Test names describe what they check [SIGNED]
- sign-off (pass): Names match content: test_owner_continuation/default_ttl/include_scope/include_paths/quoted_parentheses/escaped_case/escaped_label_length/canonical_order/rrset_ttl/zonemd/reference_zone each run the cases.json group of the same name (tests/test_outputs.py:107-158).

### 44 - Fail-closed tests carry a positive control [SIGNED]
- sign-off (pass): Fail-closed error expectations (exit 1 cases) sit in the same groups as positive cases that must compile to exact listings, e.g. escaped_label_length has 63-octet accept and 64-octet reject cases (docstring :138), quoted_parentheses has accepted quoted strings plus a real unbalanced paren error (:128).

### 47 - description/keywords/authors/category/tags accurate [SIGNED]
- sign-off (pass): task.toml: description `Make a C DNS master-file compiler follow its documented rules for owners, default TTLs, includes, escapes, canonical record order and the RFC 8976 ZONEMD digest` is accurate; keywords dns/zone-files/c/zonemd/canonical-order and tags dns/master-files/rfc4034/rfc8976/ttl-defaults/sha384 match the code; authors anonymous; category debugging (root-cause repair); languages [c]; codebase_size small (43 env files).

### 51 - Every rubric line maps to a test or instruction [SIGNED]
- warn: rubric line "Agent adds the second SHA-384 padding block when fewer than 16 bytes remain for the 128-bit length" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent special-cases names, zones or files quoted in the instruction or found in /app/examples" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent reruns an identical failing command three or more times in a row" maps to no test and no instruction sentence - confirm what grades it
- sign-off (pass): The three unmapped lines are graded by trajectory judgment, not tests: `second SHA-384 padding block` is the sha384.c fix graded by test_zonemd (the digest mismatches when buflen is 113-119, zonemd.md:32-45); `special-cases names, zones or files` and `reruns an identical failing command` are process negatives scored from each run's commands in rubric_score.txt.

### 53 - No mutually contradictory rubric lines [SIGNED]
- sign-off (pass): Read rubric.txt lines 1-22. Positives (lines 1-17) reward distinct fixes and process steps; negatives are rubric.txt:18 (external program), :19 (special-casing examples), :20 (`Agent edits /app/docs to match the existing behavior`), :21 (`Agent changes the command line, exit codes or diagnostic format`), :22 (reruns). No positive rewards an action a negative penalises: line 1 rewards reading docs while line 20 penalises editing them, and line 17 rewards rebuilding while line 21 only penalises CLI changes.

### 54 - No double-counted behavior [SIGNED]
- sign-off (pass): Each positive covers a separate defect or process step: 13 defect lines map 1:1 to the 13 fixes in solve.sh (e.g. `restores the default-TTL state` = directives.c save/restore, `makes the $TTL value in effect take precedence` = ttl.c), plus 4 process lines (read docs, reproduce, independent check, rebuild multi-file); none is counted twice.

### 70 - Each failing run's cause read from its own files [SIGNED]
- sign-off (pass): Each failing run's cause read from its own verifier output and trajectory (dumps in _reports/zonefile-master-repair/runs/run-0N.txt): run-01 fails only `--- zonemd/digest_input_near_block_end` (sha384.c never edited); run-02, run-03, run-04 fail escaped_case, escaped_label_length (both variants), the near-block-end ZONEMD case and reference_zone (name.c folding and label length untouched, sha384.c only read); run-05 fails escaped_case, the near-block-end case and reference_zone (label length fixed at its step 22 `if (lablen > LABEL_MAX) {`, folding not). No run failed because of the harness: every result.json has no exception_info and check_trajectory reported fidelity PASS for both jobs.

### 72 - NOT MET / negative verdicts cite that run's own evidence [SIGNED]
- sign-off (pass): Every NOT MET line in trajectories/run-0N/rubric_score.txt quotes that run's own files: the fold/label/padding lines quote the run's own verifier lines such as `--- escaped_case/decimal_escapes_fold_case (zonec -o example.com main.zone)` and the run's own read-only commands (run-02 `cat src/sha384.c`, run-03 `cat src/name.c`); the reproduce NOT MET lines in run-02/run-03 quote the first scratch-zone command of that run (`rm -rf /tmp/zcases && mkdir -p /tmp/zcases/sub/nested`, `tmp=$(mktemp -d); mkdir -p "$tmp/a/b"`) and its step number after the first patch. master_check's citation-quote verification found every backticked quote in the run's own corpus.

### 73 - MET verdicts spot-checked against the trajectory [SIGNED]
- sign-off (pass): Spot-checked MET verdicts against the trajectories with _reports/zonefile-master-repair/authoring/obs.py and keys.py: run-05 step 2 output contains `/tmp/zcases/sub/main.zone:7: unbalanced parentheses` (reproduce MET); run-01 and run-04 step 2 outputs start with `_sip._udp.example.net.` before the apex (reproduce MET); run-01 step 38 keystrokes contain `make clean && make` followed by `(cd /tmp && /app/build/zonec -o example /tmp/zcases/z/main.zone` and output `focused_output_stable`; run-02 step 51 output ends `integration and exit-code tests passed`; run-03 step 38 output shows `src/buf.c:76:13: error: null format string` before step 39 changed flags.

### 81 - Reward-hacking scan on every trajectory [SIGNED]
- sign-off (pass): Reward-hacking scan on all five trajectories: grep over the command dumps `grep -E '^[0-9]{3}> .*(/tests|solution|cases\.json|reward|/logs|verifier|test_outputs)' _reports/zonefile-master-repair/runs/run-0*.txt` returned no match, and master_check's own GRADING_CMD scan over the full keystrokes of every step raised no finding. No run read test files, wrote reward files or special-cased test inputs; all edits are in /app/src.

### 83 - Difficulty comes from genuine reasoning, source classified [SIGNED]
- sign-off (pass): CHALLENGE (0/5 at xhigh, bundle ee9eb7b8a0507398, jobs zonefile-master-repair-k2-20260927-052835 and -k3-20260927-055035, fidelity PASS). Difficulty source is genuine reasoning, not a trap: (1) SHA-384 padding (all 5 runs): FIPS 180-4 needs a second padding block when the 0x80 byte plus the 16-byte length no longer fit, i.e. when the final block holds 112-119 message bytes; zonec tests `if (c->buflen > 120) {` (src/sha384.c:112) instead of > 112. Every run verified its digest with Python hashlib (e.g. run-04 `h=hashlib.sha384()`), but only on small zones whose final block never holds 112-119 bytes, so the check passed and nobody questioned sha384.c; finding it needs reasoning about the length-field boundary rather than differential testing on convenient inputs. (2) \DDD case folding (4 of 5 runs): master-files.md:81-87 states escapes are decoded first and `octets A to Z become a to z, however they were written`; the agents fixed decoding paths but kept folding on the escaped text. Both rules are stated in /app/docs and the instruction points there (`The docs in /app/docs are the spec`); tests compare exact listings recomputed independently with dnspython. Nothing is hidden, ambiguous or format-trapped: all runs passed the other 7-9 groups.

## Appendix - Instruction paths (check 7)

- `/app` (instruction.md:1) -> environment/app
- `/app/docs` (instruction.md:9) -> environment/app/docs
- `/app/examples` (instruction.md:9) -> environment/app/examples
- `/app/docs/zonec.1.md` (instruction.md:11) -> environment/app/docs/zonec.1.md

## Appendix - Solution delta (checks 24-26, 30)

- `/app/src/lexer.c` via heredoc at solve.sh:7-174 -> environment/app/src/lexer.c: +9 / -9 lines
- `/app/src/name.c` via heredoc at solve.sh:177-379 -> environment/app/src/name.c: +17 / -11 lines
- `/app/src/ttl.c` via heredoc at solve.sh:382-459 -> environment/app/src/ttl.c: +4 / -4 lines
- `/app/src/directives.c` via heredoc at solve.sh:462-558 -> environment/app/src/directives.c: +3 / -3 lines
- `/app/src/zone.c` via heredoc at solve.sh:561-674 -> environment/app/src/zone.c: +7 / -8 lines
- `/app/src/zonemd.c` via heredoc at solve.sh:677-735 -> environment/app/src/zonemd.c: +2 / -2 lines
- `/app/src/sha384.c` via heredoc at solve.sh:738-863 -> environment/app/src/sha384.c: +1 / -1 lines

## Appendix - Tests (checks 35, 43)

- tests/test_outputs.py:107 test_owner_continuation - Indented records keep the previous record's owner across $ORIGIN changes (relative and absolute).
- tests/test_outputs.py:112 test_default_ttl - Records without a TTL use $TTL first, then the last written TTL, then the SOA minimum; none is an error.
- tests/test_outputs.py:117 test_include_scope - $TTL values and record TTLs inside an included file do not affect lines after the $INCLUDE.
- tests/test_outputs.py:122 test_include_paths - Relative $INCLUDE paths resolve against the including file's directory, nested and with '..', and errors name 
- tests/test_outputs.py:127 test_quoted_parentheses - Parentheses and semicolons inside quoted strings are text; a really unbalanced parenthesis is still reported.
- tests/test_outputs.py:132 test_escaped_case - Names written with \DDD escapes fold to lowercase like plain letters, in owners and in RDATA, and deduplicate.
- tests/test_outputs.py:137 test_escaped_label_length - Label length is counted in decoded octets: 63-octet escaped labels are accepted, 64-octet labels rejected at t
- tests/test_outputs.py:142 test_canonical_order - Records are sorted in RFC 4034 canonical name order, then by type code, then by RDATA wire form.
- tests/test_outputs.py:147 test_rrset_ttl - Every record of an RRset takes the TTL of the RRset's first record in input order, includes expanded in place.
- tests/test_outputs.py:152 test_zonemd - The apex ZONEMD gets the SOA serial and the RFC 8976 SHA-384 digest of the listing; other ZONEMD records are d
- tests/test_outputs.py:157 test_reference_zone - A multi-file production-style zone combining includes with origins, $TTL scopes, escapes, multi-line records a

## Appendix - Rubric map (checks 51, 54)

- `Agent reads /app/docs/master-files.md and /app/docs/output.md before editing the parser, n` (+2) -> test `test_canonical_order` (2 shared words); instruction.md:1 (3)
- `Agent reproduces at least one reported symptom by running zonec on a small zone file befor` (+2) -> test `test_quoted_parentheses` (1 shared words); instruction.md:1 (3)
- `Agent stops $ORIGIN from replacing the previous owner that indented records inherit` (+3) -> test `test_owner_continuation` (5 shared words); instruction.md:3 (4)
- `Agent makes the $TTL value in effect take precedence over the last record TTL when filling` (+3) -> test `test_default_ttl` (2 shared words); instruction.md:3 (1)
- `Agent restores the default-TTL state ($TTL value and last record TTL) when an included fil` (+3) -> test `test_default_ttl` (3 shared words); instruction.md:3 (1)
- `Agent resolves relative $INCLUDE paths against the directory of the including file using i` (+2) -> test `test_include_paths` (6 shared words); instruction.md:4 (4)
- `Agent makes the lexer treat parentheses inside quoted strings as ordinary text` (+2) -> test `test_quoted_parentheses` (5 shared words); instruction.md:4 (1)
- `Agent lowercases the decoded name octets so letters written as \DDD escapes are folded too` (+2) -> test `test_escaped_case` (4 shared words); instruction.md:3 (1)
- `Agent counts the 63-octet label limit in decoded octets instead of presentation characters` (+2) -> test `test_escaped_label_length` (4 shared words); instruction.md:1 (0)
- `Agent sorts owners in RFC 4034 canonical label order instead of comparing the printed owne` (+3) -> test `test_canonical_order` (3 shared words); instruction.md:6 (2)
- `Agent gives every record of an RRset the TTL of the RRset's first record in input order in` (+2) -> test `test_rrset_ttl` (5 shared words); instruction.md:6 (3)
- `Agent computes the ZONEMD digest only after the RRset TTLs are settled` (+2) -> test `test_include_scope` (2 shared words); instruction.md:7 (2)
- `Agent leaves only the apex ZONEMD record out of the digest while ZONEMD records below the ` (+2) -> test `test_zonemd` (4 shared words); instruction.md:6 (2)
- `Agent fills the apex ZONEMD serial from the SOA serial` (+1) -> test `test_zonemd` (3 shared words); instruction.md:6 (1)
- `Agent adds the second SHA-384 padding block when fewer than 16 bytes remain for the 128-bi` (+3) -> test `test_escaped_label_length` (1 shared words); instruction.md:7 (1)
- `Agent checks zonec's SHA-384 or ZONEMD output against an independent implementation such a` (+2) -> test `test_include_paths` (1 shared words); instruction.md:1 (2)
- `Agent rebuilds zonec after the fixes and checks its listing on a multi-file zone run from ` (+3) -> test `test_reference_zone` (2 shared words); instruction.md:1 (3)
- `Agent makes zonec run named-compilezone, a Python library or any other program instead of ` (-5) -> test `test_canonical_order` (1 shared words); instruction.md:4 (2)
- `Agent special-cases names, zones or files quoted in the instruction or found in /app/examp` (-5) -> test `test_quoted_parentheses` (1 shared words); instruction.md:7 (1)
- `Agent edits /app/docs to match the existing behavior instead of fixing the code` (-3) -> test `test_canonical_order` (1 shared words); instruction.md:9 (2)
- `Agent changes the command line, exit codes or diagnostic format documented in /app/docs/zo` (-3) -> test `test_owner_continuation` (1 shared words); instruction.md:9 (2)
- `Agent reruns an identical failing command three or more times in a row` (-1) -> test `test_owner_continuation` (0 shared words); instruction.md:1 (0)

## Appendix - Runs (checks 70, 81)

- run-01: 41 steps, grading-path commands: 0, failed tests: test_zonemd
- run-02: 54 steps, grading-path commands: 0, failed tests: test_escaped_case, test_escaped_label_length, test_zonemd, test_reference_zone
- run-03: 43 steps, grading-path commands: 0, failed tests: test_escaped_case, test_escaped_label_length, test_zonemd, test_reference_zone
- run-04: 44 steps, grading-path commands: 0, failed tests: test_escaped_case, test_escaped_label_length, test_zonemd, test_reference_zone
- run-05: 45 steps, grading-path commands: 0, failed tests: test_escaped_case, test_zonemd, test_reference_zone

## Appendix - Ablation (check 30)

- `/app/src/lexer.c` removed -> reward 0.0, failing: test_quoted_parentheses, test_reference_zone
- `/app/src/name.c` removed -> reward 0.0, failing: test_escaped_case, test_escaped_label_length, test_reference_zone
- `/app/src/ttl.c` removed -> reward 0.0, failing: test_default_ttl, test_include_scope, test_rrset_ttl, test_reference_zone
- `/app/src/directives.c` removed -> reward 0.0, failing: test_owner_continuation, test_include_scope, test_include_paths, test_rrset_ttl, test_reference_zone
- `/app/src/zone.c` removed -> reward 0.0, failing: test_owner_continuation, test_default_ttl, test_include_scope, test_quoted_parentheses, test_escaped_case, test_escaped_label_length, test_canonical_order, test_rrset_ttl, test_zonemd, test_reference_zone
- `/app/src/zonemd.c` removed -> reward 0.0, failing: test_zonemd, test_reference_zone
- `/app/src/sha384.c` removed -> reward 0.0, failing: test_zonemd
