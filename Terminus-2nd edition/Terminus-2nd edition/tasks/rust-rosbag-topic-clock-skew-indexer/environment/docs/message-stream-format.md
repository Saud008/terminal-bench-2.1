# Message stream format

messages.jsonl contains one JSON object per line with topic, seq, header_stamp_ns, receive_stamp_ns, and relay_pass fields. header_stamp_ns is the sensor clock used for synchronization. receive_stamp_ns records ingress time and is not used for sync pairing.
