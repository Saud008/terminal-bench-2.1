# Calibration offset table

Per tilt scan channel string, read offset_dbz from station calibration_offsets_dbz map. corrected_dbz equals raw_dbz plus offset_dbz rounded to two decimals. Subtracting the offset is invalid.

Surveillance and reflectivity channels may carry different offsets on the same bundle. Apply the offset matching each tilt scan channel field.
