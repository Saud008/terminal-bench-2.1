# Elevation sort order

Before materializing gates, vrstctl sorts tilt_scans by elevation_deg parsed as f64 ascending. Lexical scan_id rank is invalid. The volume metadata elevation_sequence array lists elevations in the sorted stitch sequence.

Example: tilts at 1.5 and 0.5 degrees must yield elevation_sequence [0.5, 1.5] regardless of scan_id strings.
