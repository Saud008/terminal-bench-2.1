# Bundle catalog

metro-dual-grant exercises competing priorities on overlapping UHF grants.
boundary-edge-sites places transmitters on inclusive bbox edges.
exclusion-polygon marks sites inside wildlife exclusion zones.
renewal-cutoff drops sites whose renewal_date is before as_of_date.
band-overlap-touch pairs bands that touch at 150 MHz for peer overlap counts.
tb3-priority-invert is a hidden trap bundle for empty license_id priority ranking.

TB3 overlay bundles live under /opt/verifier-fixtures/rflicat/bundles/ when the verifier sets TB3_FIXTURE_DIR.
Hidden trap bundles ship under /tests/hidden/bundles/ in the verifier harness only.
Custom render output filenames such as custom-catalog.json are allowed when tests pass an explicit --output path.

Independent expected math for bundle validation lives in /app/scripts/rf_grant_math.py.
