# Submission explanations - flatbuffers-vtable-wire-json-bundler

**Task folder:** tasks/flatbuffers-vtable-wire-json-bundler/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-28T04:15:00Z

**Category note:** Zip metadata uses `data-processing` (FlatBuffers vtable wire decode + JSON export pipeline). Choose **data-processing** on the platform form.

> Agent scaffold only - rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Hard because fbdecode must correctly walk signed vtable soffsets,uoffset indirection,struct padding,tag vector order,and nested parents while staging snapshot and ledger digests stay aligned under the hn55 field contract.Partial module swaps and held out traps stop single file or golden paste fixes from clearing the suite.

## Solution Explanation

The oracle installs corrected wire,vtable,table,vector,fingerprint,staging,export,ledger,runner,and guard modules then rebuilds fbdecode.Key insight is follow the docs for soffset subtraction,field absolute offsets,wire tag order,sixteen hex hn55 digests,and export through stdout_render after ledger alignment instead of sorting tags in the legacy export path.

## Verification Explanation

The verifier rebuilds fbdecode then runs pytest against flatc parity plus independent procedural scenes.Partial oracle and fault lib probes require multi module fixes while NOP on the broken image scores zero and the full oracle scores one.
