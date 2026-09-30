# tickwheel-oncalendar-repair: 0/5 CHALLENGE justification

Bundle sha `d1f54e8a8f1c3480`, GPT-5.6 xhigh, k=5 via run_k.sh (jobs k2-20260926-181438, k3-20260926-184045), fidelity PASS on both, rewards `[0, 0, 0, 0, 0]`, tests passed per run 3, 3, 3, 3, 5 of 10. Two earlier bundles with the same code and tests (only source comments and the source-policy regex differed; shas `3691e93cd057e60f`, `56db05fb8912b545`) also measured 0/5 with 2-6 of 10 tests passing, so the result is stable across 15 trials.

## The failures are real capability, not missing information

Every failing behaviour is stated in `/app/docs`, which instruction.md:8 names as the spec, each with a worked example:

| Defect | Spec sentence | Example in the doc |
|---|---|---|
| range end trimmed to the last value reached | normalization.md:13 | `0..10/3` becomes `00..09/3` |
| `*` combined with a repetition rejected | syntax.md:92 | `*/5` is invalid, write `0/5` |
| `~` range start/end swapped | elapse.md:74 | `~1..3` in a 31-day month covers days 29 … 31 |
| two-digit years 70-99 are 19xx | syntax.md:64 | "A year value below 70 means 20xx and a value from 70 …" |
| bounds check resets only the next smaller field | elapse.md:87, 92 | `*:0/25` from 21:51 continues from 22:00 |
| stuck check adds an hour and keeps the DST flag | elapse.md:43 | Dublin `*:30` (the instruction's first symptom) |

What the trajectories show:
- run-01 (`mG4Hfd4`) and run-05 (`odZF5S4`) printed elapse.md in full, including `## End-of-month days` with the swap sentence, and still left `src/engine/matching.rs` untouched: all six `~` cases fail with output byte-identical to the shipped buggy program (compared against `oracle-nop-evidence/nop-1/test-stdout.txt`). run-05 also printed normalization.md's `## Weekdays` and `## Elements` rules and still did not trim range ends.
- run-02, run-03 and run-04 only grepped the docs for DST-related terms (`gap|fold|DST|...`) and the CLI, fixed the four named symptoms plus one or two DST issues, and stopped. They never read the syntax/normalization rules although instruction.md:8 says the docs are the spec and "That's probably not everything".
- All five runs fixed the two instruction-named symptoms that live inside failing test groups (`Sat,Sun` pair form, `Fri..Mon` rejection), so the failing groups fail on the held-out defects, not on the reported ones.

## Why identical failures are not an underspecified rule

The same cases fail in all five runs (the six `~` ranges, the seven trimmed-range normalized forms, the three `*/N` rejections, the seven 19xx years) and in each case the output is the unmodified buggy program's output. No run produced an alternative interpretation of these rules; they never changed the code paths. The rules themselves are unambiguous, carry examples, and match real systemd 252.39 output (every expected value in tests/cases.json was recorded from `systemd-analyze calendar`).

## Difficulty source (check 83)

Genuine reasoning and engineering breadth: 11 independent defects across parsing, normalization, the field-matching engine, a glibc-style mktime port and POSIX TZ footer rules, in 9 files of a 18-file Rust crate. Four are named by symptom in the instruction. The rest are only visible by reading the spec and auditing behaviour against it, which is the job the instruction describes (`make tickwheel follow them`). Two defects (the mktime gap preference and the stuck check) require reasoning about DST transitions in zones with negative DST (Europe/Dublin) and 30-minute DST (Lord Howe). No hidden requirements, no decoys, nothing outside `/app/docs`. Oracle 3/3, NOP 0/10 twice, and each of the 9 fixed files ablated alone fails its own tests (`_reports/tickwheel-oncalendar-repair/ablation.json`).
