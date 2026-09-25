# Platform rubric — wcs-tan-plate-closure-auditor

**Task folder:** tasks/wcs-tan-plate-closure-auditor/

Agent implements platclosectl hydrate-plates bind-residuals seal-closure on a Go scientific-computing baseline, +3
Agent normalizes FITS card quotes before WCS matrix extraction per fits-card-lexicon, +2
Agent assigns CRVAL1/CRVAL2 to RA/DEC without axis swap per tan-wcs-matrix-contract, +3
Agent projects pixels with FITS 1-based CRPIX subtraction only per pixel-sky-projection-contract, +3
Agent applies positive epoch RA nudge before residual comparison per epoch-proper-motion-nudge, +2
Agent excludes stars when det_mask or cat_mask carries reject bit 0x04 per quality-mask-gate, +2
Agent sorts residual matrix rows by star_id and gates seal on bind_pass per scientific-computing-workflow, +2
Agent emits closure_digest from sorted star_ids and six-decimal RMS canonical JSON, +3
Agent rebuilds platclosectl after Go source edits and honors TB3 fixture and match overrides, +1
Agent leaves decoy DSS label renderer off bind and seal hot paths, +1
Agent patches only the eight domain modules without rewriting unrelated harness files, +2
Agent modifies the shipped test or harness files, -3
Agent edits /app/docs to name broken modules or spell out fix recipes, -3
Agent copies a Rust wcspfit ingest-stage-export pipeline from a neighbor task unchanged, -5
