# Crossmatch buffer schema

Files live at /app/work/xmatch-buffer/<run-id>.jsonl. The first line is a JSON header with run_id and tolerance_arcsec. Each following line is a match row with source_id separation_arcsec delta_ra_arcsec delta_dec_arcsec and masked boolean.
