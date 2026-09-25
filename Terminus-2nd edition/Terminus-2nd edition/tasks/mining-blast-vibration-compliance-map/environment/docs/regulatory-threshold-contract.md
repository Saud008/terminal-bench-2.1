# Regulatory threshold contract

Select threshold_mm_s from limits using structure_class (residential or industrial) and blast fired_at local hour. Convert fired_at UTC to local by adding timezone_offset_hours from the survey record.

Day period is local hour 07 through 18 inclusive. Night is all other hours. Multiply the selected day_mm_s or night_mm_s by TB3_LIMIT_SCALE when that environment variable is set to a positive float; default scale is 1.0.
