# Ops contract - film edit decision list conform control plane

## Editorial conform objective

Post houses reconcile CMX360 edit decision lists against source reel manifests before online conform. The host-local control plane must prove that record spans, source handles, reel names, and offline media flags agree with bundle timecode maps and alias tables.

## Contract map

Stage and publish behavior is defined across the sibling ops docs under `/app/docs/`:

- Timecode admission and seal digest binding: `timecode-map-contract.md`
- Reel naming and source lookup: `reel-alias-registry.md`
- Telecine handle budgets: `pull-down-handles.md`
- CMX event fields and span equality: `edl-event-schema.md`
- Stage/publish lifecycle and cross-run fingerprints: `conform-workflow.md`
- Atlas export shape: `conform-atlas-schema.md`

## Failure envelope

Diagnostic categories: `df_span_drift`, `alias_orphan`, `handle_exceeds_reel`, `offline_media_note`, `telecine_pull_drift`.
