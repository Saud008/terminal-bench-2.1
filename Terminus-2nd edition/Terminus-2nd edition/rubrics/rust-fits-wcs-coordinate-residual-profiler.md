# Platform rubric — rust-fits-wcs-coordinate-residual-profiler

**Task folder:** tasks/rust-fits-wcs-coordinate-residual-profiler/

Agent strips surrounding single quotes from FITS string header card values, 3
Agent extracts CRVAL1 and CRVAL2 without swapping right ascension and declination, 3
Agent applies FITS 1-based CRPIX offsets for TAN pixel-to-sky linearization, 3
Agent propagates catalog mask_flags into detection stage catalog_mask column, 2
Agent interprets crossmatch tolerance in arcseconds not degrees, 3
Agent increments ingest_generation on repeated ingest-header for same run id, 2
Agent honors MASK_EXCLUDE on detection mask_bit and catalog mask_flags, 2
Agent computes RMS residual statistics using only non-masked matches, 3
Agent crossmatches using great-circle separation on the celestial sphere, 3
Agent exports residual atlas with audit_digest over sorted source_ids, 2
Agent rebuilds wcspfit in test.sh before pytest subprocess verification, 2
Agent uses TB3_HEADER_DIR overlay roots for hidden header bundles, 2
Agent applies TB3_MATCH_ARCSEC override for crossmatch tolerance, 2
Agent leaves FITS CTYPE values quoted in staging JSON, -2
Agent swaps CRVAL1 and CRVAL2 when building WCS staging, -3
Agent treats CRPIX as zero-based when computing pixel offsets, -3
Agent compares separation against tolerance as degrees, -3
Agent includes masked sources in RMS aggregation, -2
Agent drops catalog mask_flags when staging detections, -2
