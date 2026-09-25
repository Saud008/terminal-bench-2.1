# Plate scenario load contract

Default fixture root is `/app/fixtures/scenarios`. When `TB3_FIXTURE_DIR` is set, load
`<TB3_FIXTURE_DIR>/<scenario_id>.json` instead.

Scenario JSON fields:

- `scenario_id` (string)
- `header_cards` (array of FITS-style card lines)
- `stars` (array of star objects)
- `match_arcsec` (float; default acceptance radius)

Each star object provides `star_id`, `x_pixel`, `y_pixel`, `ra_deg`, `dec_deg`,
`epoch_year`, `det_mask`, and `cat_mask`.
