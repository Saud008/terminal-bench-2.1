# Engineering problem contract — rust-fits-wcs-coordinate-residual-profiler

This task validates astrometric alignment between a FITS-style TAN world coordinate solution and a bundled source catalog.

The wcspfit tool must parse simplified 80-column FITS header cards into a CD matrix with CRPIX and CRVAL anchors, linearize detector pixel centroids to ICRS degrees, crossmatch catalog rows using great-circle separation in arcseconds, honor bitmask exclusions on detections and catalog flags, and emit a residual atlas with per-source delta RA and delta DEC in arcseconds plus RMS summaries over active matches.

Verifier contracts require FITS 1-based CRPIX semantics, deterministic match source_rank by source_id, wcs_revision persistence on WCS cache files, and audit_digest over sorted source identifiers.

The plate-model decoy module is outside the atlas hot path and must not participate in crossmatch or residual profiling.
