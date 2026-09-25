# Merge ledger and EAPI die hooks

Full package runs use --phase full. That runs src_install, then src_test, then updates the merge ledger at /app/state/merge-ledger.json before returning.

## Merge ledger rules

The ledger is a JSON object with a records array. Each record contains package (string), status (string), and eapi (integer).

Write a merge record only when src_test succeeds. On src_test failure the ledger must remain unchanged for that package (no new record appended). Successful runs append one record with status merged.

When src_test fails, run_full must exit non-zero and must not append any ledger record for that package.

## src_test kinds

manifest.json may define src_test with a kind field:

- path_test — verify a path exists under D and optional executable flag
- die_subshell — invoke the EAPI die helper from a subshell; the phase driver must treat the failure as fatal for the full run
- forced_fail — always fail src_test

## EAPI die helper

The die helper lives in /app/lib/ebuild-phase/die.sh. When src_test or internal QA calls ebuild_die with a message, the error must propagate to the phase driver even when the call occurs inside a subshell group ( ... ). A subshell must not swallow the failure.

EAPI level is read from manifest eapi and /app/config/eapi.conf. Packages with eapi 8 require strict die propagation.

## Full run exit status

run_full returns 0 only when src_install and src_test both succeed and a merged record is written. Any src_test failure returns non-zero with no ledger write.
