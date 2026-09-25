# Severity score contract

For each non-cancelled fault:

minutes_to_breach = max_response_minutes - (roster_epoch_minute - reported_minute)

sla_urgency = max(0, 100 - minutes_to_breach). When minutes_to_breach is negative, sla_urgency is 100.

priority_score = severity_base * 100 + trapped_passengers * 50 + sla_urgency * 10 + escalation_weight from the selected SLA contract.

Pick the SLA contract with the highest tier_rank for the fault building_id.
