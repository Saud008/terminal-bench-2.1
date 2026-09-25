# Submission explanations — cmake-fetchcontent-manifest-audit

**Task folder:** tasks/cmake-fetchcontent-manifest-audit/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This milestone task builds a cmake-audit CLI pipeline for offline FetchContent dependency auditing across parse, hash audit, and install scan stages. I rated it medium because each milestone adds a layer on the same bash modules and JSON contracts in /app/docs. Agents must wire ingest snapshots, tarball digest checks, transitive closure collection, and install tree walks without breaking earlier milestones. The verifier uses independent reference walkers in pytest plus partial-module traps that swap golden scripts from the test harness. One milestone 3 test previously failed on missing golden files in the container, which masked real agent scores.

## Solution Explanation

The oracle copies golden bash modules from each milestone solution into /app/lib, then rebuilds or reruns cmake-audit subcommands in order. Parse stages ingest snapshot then export cmake-tree.json. Hash audit writes snapshot before audit JSON. Scan reads the snapshot gate and fetch_closure union across all tree files. Milestone 3 completes fetch_closure.sh and scan.sh so transitive_closure includes nested libbaz and install artifacts match the schema.

## Verification Explanation

Each milestone has its own test.sh running pytest on test_mN.py against the prebuilt /app image. Tests reset state, call cmake-audit via subprocess, and compare outputs to inline reference functions not bundled golden JSON. Milestone 3 includes a partial broken fetch_closure trap using verifier-golden scripts mounted with the tests. Protected project fixtures stay unchanged across runs. Oracle passes all milestones. NOP stays at zero on the broken baseline.
