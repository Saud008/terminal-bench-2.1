# Submission explanations - bird-aspath-filter-peer-cutover-witness

**Task folder:** tasks/bird-aspath-filter-peer-cutover-witness/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-29T01:45:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `system-administration` (host-local bgpcut BGP peer-cutover witness: wave admission → filter/path/MED gates → sealed cutover export). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior `build-and-dependency-management` upload failed Harbor `[category_classifier]` as blocked `software-engineering`.

## Difficulty Explanation

Hard because wave rank,filter inheritance,path match modes,community rewrite exclusions,MED clamp,and critical deny RIB restore span several Go modules so a partial change looks fine on one peer inventory while abort restore or seal order still fails elsewhere.Graded rules live in instruction.md while /app/docs stay schema pointers,so agents cannot skim fixture notes for the abort peer or hidden paths.

## Solution Explanation

The oracle installs golden rank,filter,pathmatch,comms,metric,engine,salt,and report modules then rebuilds bgpcut and runs cutover on the same peer fixtures agents see.Key insight is follow the instruction cutover rules for wave order inheritance rewrite clamp and abort restore instead of patching one module around symptoms.

## Verification Explanation

test.sh rebuilds bgpcut from /app then pytest drives only the binary via subprocess against independent contract math.Helper-only unit checks and an autouse rebuild fixture are gone so an untouched baseline cannot clear free presence or math-only cases.NOP scores zero and the oracle modules clear the suite.
