# Epoch proper-motion nudge

Before residual comparison, adjust catalog RA to the plate epoch using a laboratory
constant proper-motion proxy of `0.012` arcseconds per year:

`target_ra_deg = ra_deg + (0.012 * (epoch_year - plate_EPOCH)) / 3600`

Declination is unchanged by this nudge. The sign is positive for `(star_epoch - plate_epoch)`.
