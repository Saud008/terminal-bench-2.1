# Residual bind policy

For each non-excluded star:

1. Project the detection pixel to `(pred_ra, pred_dec)`.
2. Form `target_ra` via the epoch nudge against catalog `ra_deg`.
3. Compute `delta_ra_arcsec = (pred_ra - target_ra) * 3600`
   and `delta_dec_arcsec = (pred_dec - dec_deg) * 3600`.
4. Separation uses the local tangent-plane metric
   `sep_arcsec = hypot(delta_ra_arcsec, delta_dec_arcsec)`.
5. Accept the star when `sep_arcsec <= match_arcsec`, where `match_arcsec` comes from the
   scenario unless `TB3_MATCH_ARCSEC` is set.

Write accepted rows sorted by `star_id` ascending.
