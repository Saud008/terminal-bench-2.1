# Stable assign contract

Fault processing order sorts by descending priority_score, then ascending fault_id.

Technician tie-break among eligible techs uses lowest current assignment count, then ascending tech_id.

Only non-cancelled faults with a score row participate in assignment.
