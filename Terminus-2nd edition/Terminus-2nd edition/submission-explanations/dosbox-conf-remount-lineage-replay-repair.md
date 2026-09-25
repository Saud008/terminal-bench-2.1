# Submission explanations — dosbox-conf-remount-lineage-replay-repair

**Task folder:** tasks/dosbox-conf-remount-lineage-replay-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

Agents must repair four cooperating Bash libraries under `/app/lib/` so `dosbox-plan render` replays DOSBox-style conf fragments into a remount lineage JSON plan per `/app/docs/remount-contract.md`, not fix one script in isolation. Line continuation joining is broken so backslash-wrapped mount paths stay split across physical lines, and section ordering replays `[autoexec]` mounts as files appear instead of applying every `[config]` `remap_drive` directive before any mount replay. The remount engine mishandles drive remaps, skips path-prefix rewriting on `imgmount`, overwrites duplicate mounts on the same letter instead of stacking lineage entries, and always reports `stack_depth` of one. Drive validation is a no-op, so invalid letters never trigger exit code `2` with the exact `invalid drive letter: <DRIVE>` error string. Partial fixes are caught by anti-cheat tests that install only one golden library while leaving the other three broken, so fixing section order alone still fails imgmount remap fixture `003`, and fixing remount alone cannot parse `005` line continuations.

## Solution Explanation

The oracle copies golden `conf_parse.sh`, `section_order.sh`, `remount.sh`, and `validate.sh` into `/app/lib/`, normalizes line endings, and resets state via `/app/scripts/reset-state.sh`. Continuation joining concatenates trimmed continuation lines into one logical command. Section collection gathers all config rows across manifest-ordered conf files, then all autoexec rows, preserving command order within each section type. Remount replay builds the remap table from config, validates each mount drive as a single `A`–`Z` letter before remap, applies effective drive letters and leading `X:` path rewrites for both `mount` and `imgmount`, appends stacked entries when the same drive mounts again, and computes `stack_depth` as the maximum per-drive stack height. The CLI writes sorted-key JSON to the requested output path with lineage, remaps, stats, warnings, and errors, exiting `0` on success, `1` on missing inputs or empty manifests, and `2` on the first invalid drive when `fail_on_invalid_drive` is enabled in `/app/config/plan.json`.

## Verification Explanation

Twenty-three pytest cases drive `/app/bin/dosbox-plan` as a subprocess after `reset-state.sh`, comparing `/app/output/plan.json` to an independent `reference_dosbox.py` renderer that mirrors the policy docs. Eight catalog fixtures under `/app/fixtures/confs/` are parametrized for full plan equality and exit-code parity, covering basic mounts, config-before-autoexec precedence, imgmount drive and `D:` path remaps, duplicate-drive stacking, line continuations, invalid-drive failure, multi-file manifests, and interleaved sections where config remaps must win over file order. Additional tests assert specific behaviors on fixtures `002`–`006` and `008`, seed-generated conf text keyed by `VERIFIER_SEED` to block hard-coded answers, and manifest error handling for missing or empty inputs. Four anti-cheat cases swap in a single golden library against three broken stubs from `/tests/broken_lib/` and require the render output to still differ from the reference, ensuring all four modules must be correct together.
