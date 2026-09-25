# Submission explanations - sigstore-policy-controller-admission-bundle

**Task folder:** tasks/sigstore-policy-controller-admission-bundle/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-20T00:28:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is marked hard because Fulcio root bind,digest deny order,half open revoke windows,predicate equality,builder globs,and quorum counting span several Go packages so a partial fix looks fine on one pull wave while witness staging or ledger seal still fails elsewhere.

## Solution Explanation

The oracle installs golden rootbind,pindeny,revokewin,predallow,buildergate,quorumadmit,witnesswrite,and sealhex modules then rebuilds slsacip and runs attest on the same pull fixtures agents see.Key insight is follow the admission contracts for bind order revoke windows and seal fingerprints instead of patching one package around symptoms.

## Verification Explanation

Pytest drives slsacip via subprocess and recomputes expected ledgers from independent contract math kept only under tests so pasted goldens cannot pass.NOP on the baseline should score zero and the oracle modules should clear the suite.
