# Permit bundle contract

Each scenario directory contains bundle.json with scenario, planning_epoch_day, permits, inspectors, zoning_holds, blackout_windows, violations, and permit_routes arrays.

Permit rows use permit_id, district_id, permit_type, base_priority, requested_day, and deferred boolean.

Inspectors list cert_level, districts array, daily_cap, and available_day.

Randomized ids are generated at image build time and remain stable for a given scenario name.
