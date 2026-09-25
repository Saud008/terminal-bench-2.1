# Residual atlas fields

Output files end with -residual-atlas.json. Fields include run_id match_count active_count rms_ra_arcsec rms_dec_arcsec matches array and audit_digest. RMS uses only non-masked matches. audit_digest is SHA256 hex over sorted JSON with sorted source_ids, match_count, active_count, and run_id.
