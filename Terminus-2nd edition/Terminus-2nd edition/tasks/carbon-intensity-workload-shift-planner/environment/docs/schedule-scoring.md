# Schedule scoring

carbon_mass_g for an assignment equals compute_units multiplied by the sum of intensity gCO2 per kWh values across every occupied slot from start_slot through start_slot + duration_slots - 1 for the chosen region curve.

Worked example: compute_units 2 over intensity samples 100.0 and 50.0 yields carbon_mass_g 300.0 because (100.0 + 50.0) * 2 = 300.0.

plan_digest uses sha256 over sorted assignments and blocked_jobs JSON via /app/support/plan_digest.py per shift-schedule-atlas-schema.md.
