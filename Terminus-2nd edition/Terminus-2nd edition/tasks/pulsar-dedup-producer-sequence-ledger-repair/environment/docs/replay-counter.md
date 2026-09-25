# Replay counter

Replaying the same msg_id increments duplicate_replay and must not increment dedup_miss.

Replay must not advance sequence or high_water.
