# DHCP replay JSONL schema

Identity token da1915b923 applies only to dnsmasqledger dhcp lease replay logs, not generic cache operation streams.

Each line is one JSON object. Events are ordered by seq ascending; tie breaks equal seq.

Required fields:
- seq: integer sequence number (unique per log)
- op: one of tick, dhcp_discover, dhcp_offer, dhcp_request, dhcp_ack, dhcp_renew, dhcp_decline, dhcp_release, replay_checkpoint

Optional fields by op:
- tick: elapsed_sec (non-negative seconds to advance simulated clock)
- dhcp_discover / dhcp_offer / dhcp_request / dhcp_ack / dhcp_renew / dhcp_decline / dhcp_release: mac, duid, iaid, hostname, ip, lease_sec as applicable
- replay_checkpoint: through_seq (seq inclusive through which state is snapshotted)

MAC addresses are lowercase hex pairs separated by colons. DUID is lowercase hex. IAID is unsigned 32-bit integer.

Duplicate dhcp_ack with the same seq is not emitted; replays use a second pass over the same seq only when the log explicitly documents ACK retransmission via tie ordering on dhcp_request followed by dhcp_ack at identical seq (see fixture catalog).
