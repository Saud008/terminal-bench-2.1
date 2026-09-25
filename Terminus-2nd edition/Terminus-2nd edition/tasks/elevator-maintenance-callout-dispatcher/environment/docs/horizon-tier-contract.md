# SLA breach contract

breach_horizon_min stored per fault equals minutes_to_breach from urgency-ladder-contract.

When multiple SLA contracts share a building_id, select the contract with the greatest tier_rank before computing urgency.

Gold tier_rank 3 beats silver 2 beats bronze 1.
