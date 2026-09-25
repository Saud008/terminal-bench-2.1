# Sphere crossmatch policy

Separation uses great-circle geodesy on the celestial sphere in arcseconds. The default tolerance is 2.5 arcseconds unless TB3_MATCH_ARCSEC overrides it. A detection matches when separation is less than or equal to the tolerance. Matches sort by source_id for deterministic atlas write.
