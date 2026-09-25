# Speed anomaly suppression

During atlas, walk each mmsi track in stable order after snapshot. For consecutive kept points A then B, compute haversine distance in nautical miles and elapsed hours from ts_epoch. Implied speed is distance divided by hours. When implied speed exceeds AIS_MAX_SOG_KNOTS (default 45), drop point B and increment impossible_speed. Do not drop the first point of each mmsi.

Haversine uses Earth radius 3440.065 nautical miles. When elapsed hours is zero, treat implied speed as zero.
