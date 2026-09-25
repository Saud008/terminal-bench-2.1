When incl_len is less than orig_len for a packet, the capture truncated payload on disk. Before computing the next packet delta, add a penalty to the timeline:

penalty_ns = (orig_len - incl_len) * TRUNC_NS_PER_BYTE

Default TRUNC_NS_PER_BYTE is 100 nanoseconds per truncated byte unless PCAP_JITTER_TRUNC_NS is set to a positive integer.

The penalty applies to the gap between the truncated packet and the following packet in the tolerance-ordered sequence (added to delta_ns as described in timeline-normalization.md).

stats.trunc_penalty_total_ns in export output is the sum of all penalties applied.
