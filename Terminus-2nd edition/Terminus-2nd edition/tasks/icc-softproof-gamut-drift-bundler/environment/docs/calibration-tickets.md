# Calibration tickets

Tickets JSON contains tickets array. Each ticket has ticket_id, profile_id, paper_batch_id, valid_from_epoch, valid_until_epoch.

A ticket is valid at as_of when as_of is greater than or equal to valid_from_epoch and less than or equal to valid_until_epoch inclusive.

When multiple tickets match, choose lexicographically smallest ticket_id.

When a patch batch_id has no valid ticket at as_of for the staged profile_id, add TICKET_EPOCH_INVALID.
