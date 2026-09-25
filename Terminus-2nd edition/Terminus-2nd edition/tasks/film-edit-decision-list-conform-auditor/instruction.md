Post-house operators need a host-local edl-conform-audit control plane that keeps CMX360 edit-decision admission, reel-alias resolution, drop-frame span gates, telecine pull-down handle budgets, offline media suppression, and sealed conform atlas export aligned across retries. Operate edl-conform-audit under /app so stage and publish follow the ops contracts in /app/docs/conform-workflow.md, /app/docs/edl-event-schema.md, /app/docs/timecode-map-contract.md, /app/docs/reel-alias-registry.md, /app/docs/pull-down-handles.md, /app/docs/conform-atlas-schema.md, and /app/docs/engineering-problem-contract.md.

edl-conform-audit stage --bundle PATH must load a bundle manifest, admit CMX events under the docs above, and write /app/state/edl-conform-sealed.json with seal_digest stable when the bundle fingerprint is unchanged.

edl-conform-audit publish --bundle NAME --output PATH must publish /app/output/conform-atlas.json from the sealed snapshot only. Atlas fields, diagnostic categories, and digest binding follow /app/docs/conform-atlas-schema.md and /app/docs/timecode-map-contract.md.

Cross-run behavior uses /app/state/run-seq.json with bundle fingerprints. Re-sealing an unchanged bundle must keep run_seq stable and reproduce identical seal_digest values.

Binary path: /app/scripts/edl-conform-audit (also installed as /usr/local/bin/edl-conform-audit). Do not edit /app/docs/, /app/fixtures/, or /app/config/.

Example:

/app/scripts/reset-state.sh
/app/scripts/edl-conform-audit stage --bundle /app/fixtures/bundles/df-cross-cut/bundle.json
/app/scripts/edl-conform-audit publish --bundle df-cross-cut --output /app/output/conform-atlas.json
/app/scripts/edl-conform-audit stage --bundle /app/fixtures/bundles/alias-reverse/bundle.json
/app/scripts/edl-conform-audit publish --bundle alias-reverse --output /app/output/conform-atlas.json

Exit 0 on success. Exit 2 when the bundle manifest path is absent, for example stage --bundle /app/fixtures/bundles/missing-bundle.json. Exit 3 when publish runs before a matching stage snapshot exists.
