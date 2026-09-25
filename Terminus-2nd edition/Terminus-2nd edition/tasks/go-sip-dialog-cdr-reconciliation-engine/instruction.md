# SIP dialog CDR playtest

Build the SIP dialog CDR playtest, an offline carrier-call playfield planner for transcript admission, Call-ID/To-tag fork traps, provisional and terminate scoring, retransmission collapse, skew-corrected billing-window fences, and sealed SQLite CDR win-condition export on the working baseline under `/app`. The planner loads transcript scenario packs, applies fork-join and provisional scoring, audits CANCEL-versus-BYE and retransmit traps, then seals `export-cdr` playtest exports when the dialog-seal win condition is met. There is no live SIP socket and no outbound network. This is a games SIP-CDR playfield playtest and sealed-ledger win-condition workflow: keep transcript admission, fork-branch traps, provisional suppression, terminate precedence, retransmit collapse, skew-corrected peak/offpeak windows, dialog-buffer staging seals, and sealed CDR atlas export aligned. It is not a data-processing pipeline, not a system-administration ops desk, not a software-engineering module rebuild, not a debugging drill, and not a build-and-dependency-management exercise.

The graded binary is `/app/bin/sipcdrctl`. Playtest verbs:

```text
sipcdrctl ingest-transcript --tenant TENANT --scenario SLUG
sipcdrctl compile-dialogs --tenant TENANT --scenario SLUG
sipcdrctl rate-billing --tenant TENANT --scenario SLUG
sipcdrctl export-cdr --tenant TENANT --scenario SLUG
```

Playfield contracts under `/app/docs/` define the enforceable win-condition rules:

- `/app/docs/callleg-branch-contract.md` — join keys and forked To-tag branches
- `/app/docs/provisional-response-contract.md` — provisional gating (no CDR without answer)
- `/app/docs/terminate-precedence-contract.md` — CANCEL versus BYE precedence
- `/app/docs/retransmit-suppression-contract.md` — retransmission collapse
- `/app/docs/clock-skew-contract.md` — skew correction before billing windows
- `/app/docs/billing-window-contract.md` — peak/offpeak window rating
- `/app/docs/cli-surface.md` — playtest verb surface and flags
- `/app/docs/sip-transcript-format.md` — transcript wire format
- `/app/docs/callleg-buffer-pipeline.md` — dialog-buffer staging artifact shape
- `/app/docs/cdr-sqlite-schema.md` — sealed SQLite CDR schema
- `/app/docs/verifier-refmath-contract.md` — reference math used by the verifier
- `/app/docs/engineering-problem-contract.md` — playfield failure modes

`ingest-transcript` writes `/app/state/dialog-buffer.json`. `compile-dialogs` updates that buffer and stamps `dialog_seal`. `rate-billing` writes `/app/work/billing-window-report.json` and refreshes staging. `export-cdr` publishes `/app/output/cdr.sqlite` and `/app/output/cdr-publish-seal.json` only from that staged playfield state when `dialog_seal` is greater than zero. Only answered dialogs with a final disposition may appear in published CDR rows. Provisional-only legs must remain absent from SQLite output. A second sealed pass on unchanged inputs must keep `cdr.sqlite` byte-stable. Policy modules live under `/app/lib/sipcdr/`; the decoy helper stays off the admit, gate, and emit path.

Bundled playfield packs live under `/app/fixtures/`. Off-catalog traps under `/opt/verifier-fixtures/sipcdrctl/` follow the same contracts. When `TB3_FIXTURE_DIR` is set, fixture roots may override for verifier-only overlays. After policy-module edits under `/app/lib/sipcdr/`, leave `/app/bin/sipcdrctl` current. Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`. Offline only.
