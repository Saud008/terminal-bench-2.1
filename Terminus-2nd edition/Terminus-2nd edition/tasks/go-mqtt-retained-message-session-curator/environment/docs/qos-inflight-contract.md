# QoS inflight contract

QoS 0 delivers immediately. QoS 1 tracks packet_id until PUBACK clears inflight. QoS 2 tracks packet_id until PUBCOMP clears inflight. Duplicate PUBLISH with the same packet_id before ack must not create a second offline ledger row.
