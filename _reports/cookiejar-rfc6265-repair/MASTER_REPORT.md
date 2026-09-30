# Master Ship Checklist - cookiejar-rfc6265-repair

Bundle sha `ca15ac0eff85402c`, generated 2026-09-27 09:47. FAIL 0, STALE 0, REVIEW 0, MANUAL 0, SIGNED 42, PASS 45

| # | Sec | Check | Mode | Status | First finding |
|---|---|---|---|---|---|
| CI | - | CI / pool static gates (pinned deps, base image, test.sh, docstrings, ruff, diversity) | auto | **SIGNED** | [diversity] 0/5 solved = CHALLENGE — needs a written justification that the failure is real capability |
| 0 | A | Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens | assist | **SIGNED** |  |
| 1 | A | Every stated requirement is exercised by a test | assist | **SIGNED** |  |
| 2 | A | Every requirement a test enforces is stated | assist | **SIGNED** |  |
| 3 | A | No implementation-step ('how') sentences | assist | **SIGNED** |  |
| 4 | A | Interface contracts named in the prompt are really graded | manual | **SIGNED** |  |
| 5 | A | No grader / test-suite / pipeline terms | auto | **PASS** |  |
| 6 | A | Stated constants match tests byte for byte | assist | **SIGNED** | instruction.md:8 states `2011` but no equal literal exists in tests/ - confirm it is enforced or purely illustrative |
| 7 | A | Every path the prompt names exists in the built image | auto | **PASS** |  |
| 8 | A | Output schema exactness in prose matches the tests | assist | **SIGNED** | instruction.md:8 exactness rule "Fix crumbjar so `crumbjar replay` prints exactly what such a jar would, for transcripts |
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
| 31 | C | Cold linux/amd64 oracle build runs cleanly | auto | **PASS** | cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-27T09:20:15 (baselines.json) |
| 32 | D | Zero individual tests pass under NOP | auto | **PASS** |  |
| 33 | D | Guard-style tests are coupled to real behavior | assist | **SIGNED** |  |
| 34 | D | NOP-passable guards coupled, not deleted | manual | **SIGNED** |  |
| 35 | D | Assertions do what names/docstrings claim | assist | **SIGNED** |  |
| 36 | D | Expected values never computed by agent-editable code | assist | **SIGNED** |  |
| 37 | D | Fixtures feeding expected values are not agent-editable | assist | **SIGNED** |  |
| 38 | D | Held-out scenarios really change the graded outcome | manual | **SIGNED** |  |
| 39 | D | Exactness rules enforced literally (set equality) | assist | **SIGNED** | instruction.md:8 "Fix crumbjar so `crumbjar replay` prints exactly what such a jar would, for transcripts other than the |
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
| 51 | F | Every rubric line maps to a test or instruction | assist | **SIGNED** | rubric line "Agent special-cases the hosts, paths or dates quoted in the instruction or /app/examples" maps to no test a |
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
- sign-off (pass): 0/5 CHALLENGE justified in _reports/cookiejar-rfc6265-repair/challenge_justification.md. All five runs (fidelity PASS, bundle ca15ac0eff85402c) pass 10/12 and fail only test_two_digit_years and test_name_value_pair. Both are single RFC 6265 (2011) rules that instruction.md:8 selects explicitly (`RFC 6265 as published in 2011 (not the 6265bis drafts)`), repeated at docs/cookies.md:5-6. Every run dumped date.rs and parse.rs, none changed the `(50..=99).contains(&year)` cutoff (run-05 even wrote `RFC 6265 adjusts all parsed years in 0..=69 by adding 2000.` in a test), and runs 02/04/05 fixed the empty-name rule and then reverted it themselves. No run hit a timeout or tool problem (cargo on PATH, only `bash: git: command not found`). task.toml difficulty is `hard`, the closest accepted label.

### 0 - Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens [SIGNED]
- sign-off (pass): instruction.md is 10 lines, 189 words (well under 1500 tokens), written as a teammate's report (`Our session replayer keeps its cookies in crumbjar`). Every absolute path is in backticks: `/app` (instruction.md:1), `/app/docs/POLICY.md`, `/app/docs`, `/app/examples` (instruction.md:8) and `/app/docs/cli.md` (instruction.md:10). The graded output is named at instruction.md:8: `crumbjar replay` must print exactly what such a jar would.

### 1 - Every stated requirement is exercised by a test [SIGNED]
- sign-off (pass): Each stated item maps to tests: host-only leak (instruction.md:3) -> test_host_only; /kb/articles cookies not coming back (instruction.md:4) -> test_default_path and test_path_boundary; far-future Expires not stored (instruction.md:5) -> test_invalid_dates (29 Feb 2000/2400) and test_two_digit_years; refreshed cookie moving to the end (instruction.md:6) -> test_replacement; RFC 6265 2011 plus POLICY.md (instruction.md:8) -> the other groups incl. test_site_limit; exact `crumbjar replay` output -> tests/test_outputs.py:65-70 runs `replay -` and compares stdout; std-only / no unsafe / no other programs (instruction.md:10) -> source policy tests/test_outputs.py:17-45; `cargo build --release` keeps working -> tests/test_outputs.py:53-57.

### 2 - Every requirement a test enforces is stated [SIGNED]
- sign-off (pass): The tests enforce: exact stdout and exit code 0 (instruction.md:8 `prints exactly what such a jar would`); Cargo.lock listing only crumbjar (instruction.md:10 `std-only Rust (no crates`); `unsafe` (instruction.md:10 `no unsafe`); `extern`/`#[link]` which cannot be used from std-only code without `unsafe` or a foreign crate; `process::Command`/`Command::new` (instruction.md:10 `don't run other programs`); `cargo build --release --offline --locked` which succeeds for a dependency-free crate (instruction.md:10). Comments are stripped before the policy runs (tests/test_outputs.py:26-28, 41), so prose is never penalised.

### 3 - No implementation-step ('how') sentences [SIGNED]
- sign-off (pass): instruction.md:3-6 are symptoms, instruction.md:8 is the target behaviour and spec, instruction.md:10 the constraints. No sentence names a file, function, data structure or algorithm to change.

### 4 - Interface contracts named in the prompt are really graded [SIGNED]
- sign-off (pass): The only interface named is `crumbjar replay` and the command line/output format in `/app/docs/cli.md` (instruction.md:8, 10). tests/test_outputs.py:65-70 runs `[binary, "replay", "-"]` with the transcript on stdin, as cli.md documents, and compares the whole stdout and the exit code.

### 6 - Stated constants match tests byte for byte [SIGNED]
- warn: instruction.md:8 states `2011` but no equal literal exists in tests/ - confirm it is enforced or purely illustrative
- sign-off (pass): `2011` at instruction.md:8 identifies which RFC 6265 text is the spec (published April 2011, docs/cookies.md:4 `(April 2011)`), as opposed to 6265bis. It is not a numeric value to reproduce. It is enforced through behaviour: test_name_value_pair expects `=abc` and `\t=tabbed` to be ignored (2011 section 5.2), where 6265bis would store them.

### 8 - Output schema exactness in prose matches the tests [SIGNED]
- warn: instruction.md:8 exactness rule "Fix crumbjar so `crumbjar replay` prints exactly what such a jar would, for transcripts other than the ones above and in" but tests/ show no set/list equality assertion
- sign-off (pass): instruction.md:8 asks for exactly the output an RFC 6265 jar with the POLICY.md limit would print; tests/test_outputs.py:70 fails a transcript when `p.returncode != 0 or p.stdout != case["stdout"]`, i.e. whole-string equality of stdout (every `get` line and every `dump` block in the cli.md format) plus exit code 0. No partial matching.

### 9 - No self-contradiction between sentences [SIGNED]
- sign-off (pass): Read instruction.md line by line: the four symptoms, `I doubt that's all of it`, the spec sentence (RFC 6265 2011 + POLICY.md, /app/docs as the spec) and the constraints do not conflict. `for transcripts other than the ones above and in /app/examples` (instruction.md:8) matches the 24 held-out transcripts in tests/cases.json.

### 10 - Prompt does not narrate each planted defect's mechanism [SIGNED]
- sign-off (pass): instruction.md:3-6 describe what a user observes (`also goes out to https://api.example.com/`, `the cookie moves to the end of the Cookie header`); none names a mechanism such as the host_only check in select.rs, the default-path slice, the creation-time reset or the year cutoff. 11 defects, 4 symptoms.

### 11 - Every environment file is required [SIGNED]
- sign-off (pass): All 34 files under environment/ were read. Dockerfile builds the image; .dockerignore keeps target/, tests/ and solution/ out; Cargo.toml/Cargo.lock are needed for `cargo build --locked`; README.md documents layout and build; data/public_suffix.dat is compiled in (src/psl.rs:6 `include_str!("../data/public_suffix.dat")`); the four docs are the spec named in instruction.md:8; examples/*.txt are named in instruction.md:8 and README.md:14; all 23 .rs files are modules reachable from src/main.rs:1-10 (`mod cli; mod cookie; mod dump; mod error; mod host; mod jar; mod psl; mod time; mod transcript; mod url;`), cookie/mod.rs:4-7, jar/mod.rs:3-6 and time/mod.rs:1-2.

### 13 - No comments echoing instruction or rubric text [SIGNED]
- sign-off (pass): Read every comment in environment/app/src (grep `//` lists them). They are neutral module docs and RFC section pointers such as select.rs:1 `//! Building the Cookie header (RFC 6265 section 5.4).` and evict.rs:1 `//! Removing cookies: expiry, and the per-site limit from docs/POLICY.md.`. None restates an instruction symptom or rubric criterion, and none hints at a defect (the earlier `deliberately` comment in date.rs was removed).

### 14 - No lore/notes doc indexing the planted defects [SIGNED]
- sign-off (pass): environment/ has no notes, history or changelog file. README.md only describes purpose, build and a layout paragraph (`src/cookie interprets a single Set-Cookie header, src/jar is the store`). The docs describe intended behaviour, not defects.

### 16 - No names that mislabel behavior [SIGNED]
- sign-off (pass): Names match what the code does: `default_path` and `path_match` (path.rs), `domain_match` and `is_ip_address` (host.rs), `parse_cookie_date` (date.rs), `is_leap` (civil.rs), `resolve` (expiry.rs, domain.rs), `set_cookie`, `cookie_header`, `enforce_site_limit`, `purge_expired`, `registrable_domain`. Buggy functions are named for their intended job, as in any real bug; none claims a different job.

### 18 - No unused module that already implements the answer [SIGNED]
- sign-off (pass): All 23 .rs files are declared (src/main.rs:1-10, cookie/mod.rs:4-7, jar/mod.rs:3-6, time/mod.rs:1-2) and each function exists once: grep finds a single `fn domain_match`, `fn default_path`, `fn path_match`, `fn parse_cookie_date`, `fn is_leap`, `fn resolve` per module, `fn enforce_site_limit`. No dead copy holds the fixed logic.

### 19 - Authoritative docs consistent with instruction.md [SIGNED]
- sign-off (pass): instruction.md:8 says RFC 6265 as published in 2011, not 6265bis, with the POLICY.md limit, and that /app/docs is the spec. docs/cookies.md:3-6 says the same (`RFC 6265 ... (April 2011) ... not the later rfc6265bis drafts`), docs/cookies.md:27 points to POLICY.md for limits, POLICY.md:20 sets `at most 6 cookies`, and cli.md/transcript.md define the formats that instruction.md:10 forbids changing. No rule differs.

### 20 - Non-authoritative docs hold no hidden graded rule [SIGNED]
- sign-off (pass): The only non-authoritative doc is environment/app/README.md. It states no cookie rule; its one command (`./target/release/crumbjar replay examples/basic.txt`) just runs an example. The public suffix list is data, described as such in docs/cookies.md:21-24.

### 23 - Decoys are reachable, fair and not labelled [SIGNED]
- sign-off (n/a): No decoys were planted: every environment file is the working program (`environment/app/src/**/*.rs`, Cargo.toml, Cargo.lock, data/public_suffix.dat), its spec (`environment/app/docs/*.md`), the examples named in instruction.md:8, README.md, or the Dockerfile/.dockerignore. MASTER_REPORT `Instruction paths` maps every named path to a real file.

### 24 - solve.sh delta listed file by file [SIGNED]
- sign-off (pass): solve.sh rewrites 11 files by heredoc (MASTER_REPORT `Solution delta`): host.rs +1 (IP hosts only match exactly), civil.rs +1/-1 (Gregorian leap rule), date.rs +2/-2 (70/69 year split), parse.rs +3/-5 (ignore a pair with no '=' or an empty name), path.rs +5/-1 (default-path and boundary path-match), domain.rs +6/-2 (public-suffix Domain equal to host becomes host-only), expiry.rs +10/-7 (last valid Max-Age before Expires), store.rs +5/-4 (keep creation-time on replacement), select.rs +5/-1 (host-only exact match), order.rs +1/-1 (creation-time tie-break), evict.rs +1/-1 (least recently accessed, then creation). Then solve.sh:516-519 rebuilds and replays the three examples.

### 25 - Every touched file maps to a requested fix (no no-op delta) [SIGNED]
- sign-off (pass): Each of the 11 touched files carries one defect, and restoring it alone drops the reward to 0 (_reports/cookiejar-rfc6265-repair/ablation.json; MASTER_REPORT `Ablation`: host.rs -> test_ip_hosts, civil.rs -> test_invalid_dates, date.rs -> test_two_digit_years, parse.rs -> test_name_value_pair, path.rs -> test_default_path/test_path_boundary, domain.rs -> test_public_suffix, expiry.rs -> test_max_age_precedence, store.rs -> test_replacement, select.rs -> test_host_only, order.rs -> test_header_order, evict.rs -> test_site_limit). Every fix is required by RFC 6265 or POLICY.md.

### 26 - No out-of-scope delta [SIGNED]
- sign-off (pass): The per-file delta (MASTER_REPORT `Solution delta`, 40 added / 25 removed lines in total) only changes the 11 defect sites; cli.rs, dump.rs, transcript.rs, url.rs, psl.rs, the docs and the PSL data are untouched, so no CLI, format or undocumented behaviour changes.

### 27 - Reference output independently re-derived [SIGNED]
- sign-off (pass): Expected outputs in tests/cases.json come from _reports/cookiejar-rfc6265-repair/refgen/refjar.py, a Python RFC 6265 + POLICY.md jar written from the RFC text and docs, not from the Rust fix: refgen/gen_cases.py:327 `out["groups"][group] = [{"transcript": t, "stdout": refjar.replay(t, PSL)} for t in transcripts]`. The fixed Rust binary and refjar.py were compared on 1500 random transcripts with refgen/fuzz.py (report line fuzz.py:98 `{len(files) - bad}/{len(files)} identical`): `1500/1500 identical`. The oracle passes 12/12 in oracle-1..3 (`12 passed`).

### 28 - Agent consensus vs reference outlier checked [SIGNED]
- sign-off (pass): Where all five runs disagree with the reference, their output equals the shipped program's (compared with oracle-nop-evidence/nop-1/test-stdout.txt): two-digit years 50-69 mapped to 19xx and `=abc` stored. The reference follows RFC 6265 section 5.1.1 steps 3-4 (70-99 -> 19xx, 0-69 -> 20xx) and section 5.2 (ignore a pair without '=' or with an empty name), which is the 2011 text instruction.md:8 selects. The reference is not the outlier.

### 31 - Cold linux/amd64 oracle build runs cleanly [PASS]
- info: cold linux/amd64 oracle x3 + nop x2 clean on 2026-09-27T09:20:15 (baselines.json)

### 33 - Guard-style tests are coupled to real behavior [SIGNED]
- sign-off (pass): The only guard is the source policy (tests/test_outputs.py:17-45). `py -3 _reports/cookiejar-rfc6265-repair/refgen/guardcheck.py` runs its own regexes and comment stripper: comments mentioning `Command::new`/`unsafe`/`extern` and the identifier `unsafe_count` -> `clean`; a real `std::process::Command::new("true")` -> `['process::Command', 'Command::new']`, `use std::process::{Stdio, Command};` -> `['process::Command']`, `unsafe { }` -> `['unsafe']`. The shipped tree and the oracle tree both pass it (oracle 12 passed).

### 34 - NOP-passable guards coupled, not deleted [SIGNED]
- sign-off (pass): No test passes under NOP: oracle-nop-evidence/nop-1 and nop-2 end `12 failed`, each failure an output mismatch (`2 of 2 transcripts differ` or `1 of 2`); the source policy passes on the shipped tree, so the guard is not the reason.

### 35 - Assertions do what names/docstrings claim [SIGNED]
- sign-off (pass): Each test (tests/test_outputs.py:79-136) has a docstring naming its behaviour, e.g. :135 `Set-Cookie headers without '=' in the first pair, or with an empty name, are ignored.`, and calls `_check_group` on exactly that group of tests/cases.json; the transcripts in each group target that behaviour (name_value_pair has `token`, `=abc`, `\t=tabbed`, `flag; Secure`).

### 36 - Expected values never computed by agent-editable code [SIGNED]
- sign-off (pass): Expected output comes only from tests/cases.json (tests/test_outputs.py:15 `CASES = json.loads((Path(__file__).parent / "cases.json")...`), which ships with the tests; nothing under /app computes it. The verifier builds into its own `CARGO_TARGET_DIR=/tmp/crumbjar-verify-target` (tests/test_outputs.py:13, 52), so a stale agent binary is not reused.

### 37 - Fixtures feeding expected values are not agent-editable [SIGNED]
- sign-off (pass): tests/cases.json is under tests/, which the image never contains (Dockerfile:22 `COPY app/ /app/`, .dockerignore:18 `tests/`); it is mounted only at verification time.

### 38 - Held-out scenarios really change the graded outcome [SIGNED]
- sign-off (pass): tests/cases.json has 24 transcripts in 12 groups (2 each). None of them is an instruction.md or /app/examples transcript; instruction hosts reappear only in new scenarios, e.g. tests/cases.json:25 `set https://example.com/ pref=1; Domain=example.com` followed by `get https://deep.api.example.com/x`. Each group decides the result: ablation.json shows restoring any single defect gives reward 0.0 with its group failing, and the five agent runs that fixed the four named symptoms but missed two unnamed rules scored 0 with test_two_digit_years and test_name_value_pair failing.

### 39 - Exactness rules enforced literally (set equality) [SIGNED]
- warn: instruction.md:8 "Fix crumbjar so `crumbjar replay` prints exactly what such a jar would, for transcripts other than the ones above and in" - no literal equality enforcement found in tests/
- sign-off (pass): tests/test_outputs.py:70 `if p.returncode != 0 or p.stdout != case["stdout"]:` records a failure and :76 `assert not failures` fails the test; stdout is compared as one full string, so order, count and content of every line must match exactly. No subset or fuzzy matching.

### 40 - Test tolerances equal the stated tolerances [SIGNED]
- sign-off (n/a): No numeric tolerances: every comparison is exact string/integer equality (tests/test_outputs.py:70) and instruction.md states no tolerance.

### 43 - Test names describe what they check [SIGNED]
- sign-off (pass): Test names match their groups (tests/test_outputs.py:79-136): test_default_path, test_path_boundary, test_host_only, test_ip_hosts, test_max_age_precedence, test_two_digit_years, test_invalid_dates, test_replacement, test_header_order, test_public_suffix, test_site_limit, test_name_value_pair.

### 44 - Fail-closed tests carry a positive control [SIGNED]
- sign-off (pass): Transcripts mix cookies the shipped program already handles with the defective case, so a jar that drops everything fails too: e.g. in name_value_pair the NOP already prints `ok=1; spaced=two words; empty=` and the expected dump keeps those three cookies; in max_age_precedence the NOP gets `1 of 2 transcripts differ` (nop-1/test-stdout.txt:384). The oracle passes all 24 transcripts (oracle-1..3 `12 passed`).

### 47 - description/keywords/authors/category/tags accurate [SIGNED]
- sign-off (pass): task.toml: description `Make a Rust cookie jar replay recorded HTTP sessions exactly like an RFC 6265 user agent with a documented per-site cookie limit` matches the task; keywords rust/cookies/rfc6265/http/public-suffix and tags http-cookies/rfc6265/cookie-date-parsing/public-suffix-list/lru-eviction describe it; category `debugging`; authors anonymous; languages ["rust"]; codebase_size `small` (34 files under environment/, >= 20).

### 51 - Every rubric line maps to a test or instruction [SIGNED]
- warn: rubric line "Agent special-cases the hosts, paths or dates quoted in the instruction or /app/examples" maps to no test and no instruction sentence - confirm what grades it
- warn: rubric line "Agent reruns an identical failing command three or more times in a row" maps to no test and no instruction sentence - confirm what grades it
- sign-off (pass): rubric.txt:16 (special-casing) is graded from the trajectory and backed by instruction.md:8 `for transcripts other than the ones above and in /app/examples`; the held-out transcripts in tests/cases.json also punish it indirectly. rubric.txt:20 (identical failing command three times) is a trajectory-hygiene criterion read from the command log (each rubric_score.txt cites it per run). The other 18 lines map to a test group or an instruction sentence (MASTER_REPORT `Rubric map`).

### 53 - No mutually contradictory rubric lines [SIGNED]
- sign-off (pass): Read all 20 rubric.txt lines pairwise. The 15 positives each name a distinct fix or process step (rubric.txt:1 `reads /app/docs ... before changing`, rubric.txt:2 `reproduces at least one reported symptom ... before editing`, rubric.txt:15 `rebuilds crumbjar and replays transcripts ... after editing`). The negatives forbid things no positive asks for: rubric.txt:17 `makes crumbjar run another program or pulls in a crate` vs rubric.txt:15 which only rebuilds crumbjar; rubric.txt:18 `edits /app/docs or /app/data/public_suffix.dat` vs rubric.txt:1 which only reads them; rubric.txt:19 `changes the command line or output format` vs no positive touching cli.rs/dump.rs; rubric.txt:20 `reruns an identical failing command three or more times` vs rubric.txt:2 which needs one reproduction. No single action earns a pair.

### 54 - No double-counted behavior [SIGNED]
- sign-off (pass): No behaviour is scored twice: rubric.txt:3 `default-path stop before the rightmost` and rubric.txt:4 `path-match require the cookie path` share path.rs but map to separate groups (test_default_path, test_path_boundary); rubric.txt:10 `keeps the old creation-time` (store.rs, test_replacement) vs rubric.txt:11 `orders equal-length cookie paths ... by creation-time` (order.rs, test_header_order); rubric.txt:5 `restricts host-only cookies` (select.rs, test_host_only) vs rubric.txt:12 `turns a Domain attribute equal to a request host ... into a host-only cookie` (domain.rs, test_public_suffix); rubric.txt:2 (before editing) vs rubric.txt:15 (after editing).

### 70 - Each failing run's cause read from its own files [SIGNED]
- sign-off (pass): Read from each run's verifier/test-stdout.txt and agent/trajectory.json (commands dumped to _reports/cookiejar-rfc6265-repair/cmds/run-0N.txt). All five fail test_two_digit_years (date.rs cutoff never edited; got `-- jar @1767225600: 2 cookie(s)` instead of 4, and 0 instead of 1 for `late=1; expires=06 nov 68`) and test_name_value_pair (got header `=abc; ok=1; spaced=two words; empty=`). run-01/03 only rejected a missing '=' (`pair.split_once('=')?`, `None => return None,`); run-02 reverted its own fix in step 6; run-04 had `if name.is_empty() {` in step 5 and restored `name.is_empty() && value.is_empty()` in step 6; run-05 had the full rule in step 6 and reverted in steps 7 and 14.

### 72 - NOT MET / negative verdicts cite that run's own evidence [SIGNED]
- sign-off (pass): Every NOT MET and negative line in the five rubric_score.txt files carries a backticked fragment from that run's own trajectory.json or test-stdout.txt (master_check check 72 reports no `cites no quote` errors after the fixes), e.g. run-04 line 14 cites its own step-6 `if name.is_empty() && value.is_empty() {` restore, run-02 line 18 its own `for f in docs/*; do printf '\n--- %s ---\n' "$f"; cat "$f"; done`, run-05 line 8 its own test comment `RFC 6265 adjusts all parsed years in 0..=69 by adding 2000.`.

### 73 - MET verdicts spot-checked against the trajectory [SIGNED]
- sign-off (pass): Every MET verdict for a code fix (lines 3-7, 9-13) matches a PASSED line for the mapped test in that run's test-stdout.txt (all five: 10 PASSED, the same 2 FAILED). master_check check 73 no longer reports any quote missing from a run's files. Spot-checked: run-01 line 10 `let created = self.cookies[i].created;` in its step-4 store.rs heredoc plus `PASSED ../tests/test_outputs.py::test_replacement`; run-04 line 15 step-5 replays of /tmp/edge.txt, /tmp/evict.txt and the examples after `cargo build --release`; run-03 line 13 `c1 is least recently accessed` in its /tmp/evict.txt.

### 81 - Reward-hacking scan on every trajectory [SIGNED]
- sign-off (pass): `py -3 _reports/cookiejar-rfc6265-repair/refgen/guardcheck.py` scans every trajectory.json for /tests/, test_outputs.py, ctrf.json, reward.txt, /logs/verifier and /solution/: `run-01 []` ... `run-05 []` (MASTER_REPORT `Runs`: grading-path commands 0 in every run). No output artifact was hand-written: all changes are Rust source edits under /app/src followed by `cargo build --release`. truncated=0 in every run_k trial line, and each run ends with task_complete, not a crash.

### 83 - Difficulty comes from genuine reasoning, source classified [SIGNED]
- sign-off (pass): Source classified as genuine reasoning and spec discipline: 11 defects across cookie-date parsing, calendar code, Set-Cookie parsing, domain/path matching, storage, header ordering and a bespoke per-site LRU policy. 4 are named by symptom; the rest must be found by auditing the code against the 2011 RFC and POLICY.md (instruction.md:8). The two rules every run missed are standard RFC 6265 rules that differ from 6265bis/modern habits. No obscurity (public RFC plus docs), no decoys, no contradictions, no compliance wall (the constraints are one sentence). Details: _reports/cookiejar-rfc6265-repair/challenge_justification.md.

## Appendix - Instruction paths (check 7)

- `/app` (instruction.md:1) -> environment/app
- `/app/docs/POLICY.md` (instruction.md:8) -> environment/app/docs/POLICY.md
- `/app/docs` (instruction.md:8) -> environment/app/docs
- `/app/examples` (instruction.md:8) -> environment/app/examples
- `/app/docs/cli.md` (instruction.md:10) -> environment/app/docs/cli.md

## Appendix - Stated constants (checks 6, 40)

- instruction.md:8 `2011` -> NOT in tests/

## Appendix - Solution delta (checks 24-26, 30)

- `/app/src/host.rs` via heredoc at solve.sh:6-30 -> environment/app/src/host.rs: +1 / -0 lines
- `/app/src/time/civil.rs` via heredoc at solve.sh:32-70 -> environment/app/src/time/civil.rs: +1 / -1 lines
- `/app/src/time/date.rs` via heredoc at solve.sh:72-168 -> environment/app/src/time/date.rs: +2 / -2 lines
- `/app/src/cookie/parse.rs` via heredoc at solve.sh:170-269 -> environment/app/src/cookie/parse.rs: +3 / -5 lines
- `/app/src/cookie/path.rs` via heredoc at solve.sh:271-292 -> environment/app/src/cookie/path.rs: +5 / -1 lines
- `/app/src/cookie/domain.rs` via heredoc at solve.sh:294-335 -> environment/app/src/cookie/domain.rs: +6 / -2 lines
- `/app/src/cookie/expiry.rs` via heredoc at solve.sh:337-360 -> environment/app/src/cookie/expiry.rs: +10 / -7 lines
- `/app/src/jar/store.rs` via heredoc at solve.sh:362-430 -> environment/app/src/jar/store.rs: +5 / -4 lines
- `/app/src/jar/select.rs` via heredoc at solve.sh:432-470 -> environment/app/src/jar/select.rs: +5 / -1 lines
- `/app/src/jar/order.rs` via heredoc at solve.sh:472-482 -> environment/app/src/jar/order.rs: +1 / -1 lines
- `/app/src/jar/evict.rs` via heredoc at solve.sh:484-514 -> environment/app/src/jar/evict.rs: +1 / -1 lines

## Appendix - Tests (checks 35, 43)

- tests/test_outputs.py:79 test_default_path - Cookies without a usable Path attribute get the directory of the request path as their path.
- tests/test_outputs.py:84 test_path_boundary - A cookie path only matches request paths that continue it at a '/' boundary.
- tests/test_outputs.py:89 test_host_only - Cookies set without a Domain attribute go back only to the exact host that set them.
- tests/test_outputs.py:94 test_ip_hosts - IP-address hosts only domain-match themselves, so suffix Domain attributes from them are ignored.
- tests/test_outputs.py:99 test_max_age_precedence - Max-Age decides the lifetime over Expires regardless of attribute order; invalid Max-Age is skipped.
- tests/test_outputs.py:104 test_two_digit_years - Two-digit years in Expires map 70-99 to 19xx and 00-69 to 20xx.
- tests/test_outputs.py:109 test_invalid_dates - Expires dates that do not exist on the Gregorian calendar are ignored; real leap days are kept.
- tests/test_outputs.py:114 test_replacement - Replacing a cookie keeps the old creation-time, which shows in header order and the dump.
- tests/test_outputs.py:119 test_header_order - Cookie header lists longer paths first and equal paths by creation-time.
- tests/test_outputs.py:124 test_public_suffix - Domain attributes naming a public suffix are refused, except when it is the request host itself.
- tests/test_outputs.py:129 test_site_limit - Per-site limit of docs/POLICY.md evicts the least recently accessed cookie of the site.
- tests/test_outputs.py:134 test_name_value_pair - Set-Cookie headers without '=' in the first pair, or with an empty name, are ignored.

## Appendix - Rubric map (checks 51, 54)

- `Agent reads /app/docs (cookies.md, POLICY.md, cli.md) before changing the cookie, jar or t` (+2) -> test `test_site_limit` (3 shared words); instruction.md:1 (1)
- `Agent reproduces at least one reported symptom with crumbjar replay on a transcript before` (+2) -> test `test_replacement` (1 shared words); instruction.md:8 (3)
- `Agent makes the default-path stop before the rightmost "/" of the request path` (+2) -> test `test_default_path` (3 shared words); instruction.md:8 (1)
- `Agent makes path-match require the cookie path to end in "/" or be followed by "/" in the ` (+2) -> test `test_path_boundary` (4 shared words); instruction.md:1 (1)
- `Agent restricts host-only cookies (stored with no Domain attribute) to the exact host that` (+3) -> test `test_host_only` (6 shared words); instruction.md:5 (2)
- `Agent stops IP-address hosts from domain-matching a shorter suffix` (+2) -> test `test_ip_hosts` (5 shared words); instruction.md:1 (0)
- `Agent lets the last valid Max-Age decide the lifetime whenever one is present, ahead of an` (+2) -> test `test_max_age_precedence` (3 shared words); instruction.md:5 (1)
- `Agent maps two-digit cookie-date years 70-99 to 1970-1999 and 00-69 to 2000-2069` (+2) -> test `test_two_digit_years` (2 shared words); instruction.md:1 (1)
- `Agent corrects the Gregorian leap-year rule so 29 February exists in 2000 and 2400 but not` (+2) -> test `test_invalid_dates` (3 shared words); instruction.md:1 (0)
- `Agent keeps the old creation-time when a cookie with the same name, domain and path is rep` (+3) -> test `test_replacement` (5 shared words); instruction.md:1 (3)
- `Agent orders equal-length cookie paths in the Cookie header by creation-time` (+2) -> test `test_header_order` (7 shared words); instruction.md:6 (2)
- `Agent turns a Domain attribute equal to a request host that is itself a public suffix into` (+2) -> test `test_public_suffix` (7 shared words); instruction.md:1 (1)
- `Agent evicts the least recently accessed cookie of the site, ties by creation-time, when t` (+3) -> test `test_site_limit` (7 shared words); instruction.md:1 (1)
- `Agent ignores Set-Cookie headers whose first pair has no "=" or has an empty name` (+2) -> test `test_name_value_pair` (7 shared words); instruction.md:6 (2)
- `Agent rebuilds crumbjar and replays transcripts covering the fixed behaviors after editing` (+3) -> test `test_replacement` (1 shared words); instruction.md:8 (3)
- `Agent special-cases the hosts, paths or dates quoted in the instruction or /app/examples` (-5) -> test `test_path_boundary` (1 shared words); instruction.md:5 (1)
- `Agent makes crumbjar run another program or pulls in a crate instead of fixing its own log` (-5) -> test `test_default_path` (0 shared words); instruction.md:8 (2)
- `Agent edits /app/docs or /app/data/public_suffix.dat to match the existing behavior instea` (-3) -> test `test_ip_hosts` (2 shared words); instruction.md:8 (1)
- `Agent changes the command line or output format documented in /app/docs/cli.md` (-3) -> test `test_site_limit` (1 shared words); instruction.md:8 (3)
- `Agent reruns an identical failing command three or more times in a row` (-1) -> test `test_default_path` (0 shared words); instruction.md:1 (0)

## Appendix - Runs (checks 70, 81)

- run-01: 7 steps, grading-path commands: 0, failed tests: test_two_digit_years, test_name_value_pair
- run-02: 8 steps, grading-path commands: 0, failed tests: test_two_digit_years, test_name_value_pair
- run-03: 10 steps, grading-path commands: 0, failed tests: test_two_digit_years, test_name_value_pair
- run-04: 11 steps, grading-path commands: 0, failed tests: test_two_digit_years, test_name_value_pair
- run-05: 16 steps, grading-path commands: 0, failed tests: test_two_digit_years, test_name_value_pair

## Appendix - Ablation (check 30)

- `/app/src/host.rs` removed -> reward 0.0, failing: test_ip_hosts
- `/app/src/time/civil.rs` removed -> reward 0.0, failing: test_invalid_dates
- `/app/src/time/date.rs` removed -> reward 0.0, failing: test_two_digit_years
- `/app/src/cookie/parse.rs` removed -> reward 0.0, failing: test_name_value_pair
- `/app/src/cookie/path.rs` removed -> reward 0.0, failing: test_default_path, test_path_boundary
- `/app/src/cookie/domain.rs` removed -> reward 0.0, failing: test_public_suffix
- `/app/src/cookie/expiry.rs` removed -> reward 0.0, failing: test_max_age_precedence
- `/app/src/jar/store.rs` removed -> reward 0.0, failing: test_replacement, test_site_limit
- `/app/src/jar/select.rs` removed -> reward 0.0, failing: test_host_only, test_replacement, test_public_suffix, test_site_limit
- `/app/src/jar/order.rs` removed -> reward 0.0, failing: test_default_path, test_host_only, test_two_digit_years, test_replacement, test_header_order, test_name_value_pair
- `/app/src/jar/evict.rs` removed -> reward 0.0, failing: test_site_limit
