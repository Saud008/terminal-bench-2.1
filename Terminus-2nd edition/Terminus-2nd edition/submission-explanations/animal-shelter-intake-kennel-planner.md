# Submission explanations — animal-shelter-intake-kennel-planner

**Task folder:** tasks/animal-shelter-intake-kennel-planner/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire bind, weave, and seal for shelter intake while kennel compatibility, vaccination windows, quarantine dates, adoption holds, and transfer penalties interact. Contracts live in several /app/docs files rather than the short instruction. A fix in one module can pass bundled scenarios yet fail hidden fixture paths or a stable rerun.

## Solution Explanation

The oracle applies sed fixes plus registrylock and sealatlas rewrites, rebuilds intakectl, and runs bind-weave-seal against the same fixtures agents see. The work aligns digest attestation, weave staging headers, transfer tie-breaks, vaccine eligibility, and seal publish ordering with the doc contracts. Priority scoring and quarantine window checks must match the reference math in the verifier helpers.

## Verification Explanation

test.sh rebuilds intakectl before pytest. Nineteen tests invoke /app/bin/intakectl through subprocess calls. shelter_planner_sim recomputes expected placements and transfers from SQLite and JSONL fixtures. Two hidden probe directories catch shallow single-file fixes.
