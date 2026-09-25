# Batch ack policy

Batch publish advances high_water and accepted_count only for events with broker_ack true.

Partial broker failure must not advance high_water for failed events in the batch.

Failed broker_ack events increment dedup_miss and must not mark msg_id as seen.
