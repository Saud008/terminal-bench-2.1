# Peer dampening table

File policies/PEER.json fields:

peer_id, suppress_threshold default 2000, reuse_threshold default 750, half_life_ms default 300000, flap_penalty default 1000, max_penalty default 16000.

reuse_threshold times two must stay below suppress_threshold.

advance must read reuse_threshold from peer_table entry, never overwrite with a global constant.

TB3_HALF_LIFE_BIAS adds to half_life_ms when normalize loads policies.
