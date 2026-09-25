The mock Portage-style ebuild phase driver under /app is failing src_install and full package runs on the bundled sample packages in /app/fixtures. Repair the bash libraries under /app/lib/ebuild-phase so behavior matches the phase order and QA rules in /app/docs/ebuild-phase-order.md and /app/docs/qa-checks.md, and so --phase full obeys /app/docs/merge-ledger.md and propagates EAPI die failures from subshells as described in /app/docs/cli-reference.md.

After src_install succeeds, the installed tree under the destination root must pass all QA checks, preserve setuid bits where the manifest requests them, and keep symbolic links contained inside the destination. The driver must record each src_install step in /app/state/phase-trace.json, using the order required by the contract docs.

When src_test fails, run_full must exit non-zero and must not append any merge record for that package in /app/state/merge-ledger.json; when src_test invokes the die helper inside a subshell, the failure must abort the full run. Successful full runs append exactly one merged record.

Hidden verifier package trees are only available when TB3_PACKAGE_ROOT points at an absolute directory containing extra sample packages. Bundled public samples remain under /app/fixtures.

Use /app/bin/ebuild-phase with --phase src_install or --phase full. Reset state with /app/scripts/reset-state.sh between verifier runs when needed.
