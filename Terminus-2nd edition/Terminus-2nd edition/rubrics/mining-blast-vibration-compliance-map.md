# Platform rubric — mining-blast-vibration-compliance-map

**Task folder:** tasks/mining-blast-vibration-compliance-map/

Agent writes peak correlation buffer at /app/state/peak-correlation-buffer.json on load-survey, +3
Agent increments correlate_seq on each load-survey pass, +3
Agent applies distance attenuation with reference distance in numerator, +3
Agent subtracts zero offset before applying sensor gain, +3
Agent measures compliance distance to nearest parcel boundary vertex, +3
Agent selects night regulatory threshold outside day window hours, +3
Agent blends corrected and attenuated PPV with max not min, +3
Agent sorts exceedance rows by property_id blast_id sensor_id, +2
Agent computes atlas_digest from summary and rounded exceedance values, +3
Agent publishes atlas JSON to caller output path under /app/output/, +2
Agent rebuilds seismocomply with cargo release locked before pytest, +2
Agent honors TB3_FIXTURE_DIR for hidden survey overlays, +2
Agent honors TB3_LIMIT_SCALE for night threshold scaling traps, +2
Agent leaves correlate_seq stuck at zero across correlate passes, -3
Agent applies gain before zero offset subtraction, -3
Agent uses parcel centroid instead of boundary vertex distance, -3
Agent picks day limit during night blast timestamps, -2
Agent sorts exceedance rows by blast_id only, -2
