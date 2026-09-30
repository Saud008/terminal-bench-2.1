# cookiejar-rfc6265-repair - 0/5 CHALLENGE justification

Measured on bundle sha ca15ac0eff85402c: GPT-5.6 xhigh, run_k k=2 (cookiejar-rfc6265-repair-k2-20260927-035514) + k=3 (cookiejar-rfc6265-repair-k3-20260927-040130), fidelity PASS on all five trials, rewards [0, 0, 0, 0, 0]. Every trial passed 10/12 tests and failed the same two: `test_two_digit_years` and `test_name_value_pair`.

## The two failing rules are stated, not hidden

- instruction.md:8 fixes the spec as `RFC 6265 as published in 2011 (not the 6265bis drafts)`; docs/cookies.md:3-6 repeats it (`It follows that RFC as published, not the later rfc6265bis drafts`).
- RFC 6265 section 5.1.1 steps 3-4: years 70-99 get 1900 added, 0-69 get 2000 added. crumbjar uses a 50/49 split (environment/app/src/time/date.rs:85-89 `if (50..=99).contains(&year)`). Nothing in /app/docs overrides the RFC here.
- RFC 6265 section 5.2: a name-value-pair without "=" means the whole set-cookie-string is ignored, and so does an empty name. crumbjar keeps nameless cookies (environment/app/src/cookie/parse.rs:56-62), which is the 6265bis behaviour the instruction explicitly excludes.
- The instruction's third symptom (`some cookies with perfectly good far-future Expires dates are never stored`) is caused by both the leap-year bug and the year cutoff (a 2055 expiry written `55` becomes 1955 and is dropped as expired). Hidden transcripts in the `two_digit_years` group exercise exactly that.

## What the agents did (read from each run's own files)

- All five read /app/docs in full and read date.rs and parse.rs (they are in the `for f in src/cookie/*.rs src/jar/*.rs src/time/*.rs; do ... cat` dumps), then fixed 10 of the 12 behaviours.
- Year cutoff: no run edited the cutoff lines. run-05 even wrote the RFC rule into a test comment (`RFC 6265 adjusts all parsed years in 0..=69 by adding 2000.`) but never checked the code against it. The agents stopped at the leap-year cause of symptom three and never looked for a second one.
- Empty names: run-01 and run-03 only rejected the missing "=". run-02, run-04 and run-05 had the fully correct rule at some point and then reverted it themselves (run-04 step 6 restores `if name.is_empty() && value.is_empty() {`, run-05 step 14 goes back to the shipped line). That is the 6265bis-era behaviour winning over the 2011 text the instruction points to.
- Every run finished in 7-16 steps and declared completion. None hit the timeout (7200 s) or a tooling problem: `cargo` was on PATH in every run (after the /etc/profile.d/cargo.sh fix) and the only `command not found` was `git`, which the task doesn't need.

## Why this is a capability gap, not a task defect

- Both behaviours are single, well-known RFC rules. The reference implementation (_reports/cookiejar-rfc6265-repair/refgen/refjar.py, written independently of the Rust fix) and the oracle agree on 1500/1500 random transcripts, and the oracle passes 12/12 in three cold runs.
- The docs contain no statement that contradicts either rule (grep of /app/docs for years, cutoff and name handling finds nothing but `(April 2011)` at cookies.md:4).
- The failure mode is consistent and diagnosable: the agents audit the code against their memory of modern cookie behaviour instead of against the version of the spec they were told to use, and they stop at the first cause of a symptom.
- task.toml difficulty is `hard`, the closest accepted label. The same precedent is tickwheel-oncalendar-repair (0/5, `hard`).
