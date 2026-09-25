Task identity 5a4c8ea9f4 defines the engineering problem for rust fits wcs coordinate residual profiler. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Observatory calibration teams must compare FITS header world-coordinate solutions against source catalogs and publish residual atlases for nightly astrometry QA. Build wcspfit on the working Rust codebase under /app to parse FITS-style header cards, buffer astrometric state on disk, crossmatch pixel centroids to catalog coordinates with geodesy-aware separation, and emit deterministic residual atlas JSON under /app/output/.

Install wcspfit at /app/bin/wcspfit with subcommands parse-header, buffer-detections, crossmatch, and profile-residuals. CLI flags, on-disk artifact layouts, bitmask semantics, and numeric contracts are defined only in /app/docs/fits-card-grammar.md, /app/docs/wcs-tan-matrix-contract.md, /app/docs/pixel-sky-linearization.md, /app/docs/catalog-epoch-shift.md, /app/docs/sphere-crossmatch-policy.md, /app/docs/mask-bit-exclude-contract.md, /app/docs/wcs-cache-schema.md, /app/docs/xmatch-buffer-schema.md, /app/docs/residual-atlas-fields.md, /app/docs/fixture-bundle-catalog.md, and /app/docs/pytest-verifier-primitives.md.

Bundled fixtures live under /app/fixtures/. Runtime header overlays honor TB3_HEADER_DIR for alternate header roots. Match tolerance overrides honor TB3_MATCH_ARCSEC for alternate arcsecond thresholds from /app/config/wcspfit.json. Pytest-side math and hashlib usage follows /app/docs/pytest-verifier-primitives.md.

Compile wcspfit with /usr/local/cargo/bin/cargo build --release --locked from /app and install the binary to /app/bin/wcspfit from /app/target/release/wcspfit. Run /app/scripts/reset-workspace.sh before cross-run verifier cases.
