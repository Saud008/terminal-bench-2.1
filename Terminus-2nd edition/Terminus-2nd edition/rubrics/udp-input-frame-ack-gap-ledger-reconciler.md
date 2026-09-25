# Platform rubric — udp-input-frame-ack-gap-ledger-reconciler

**Task folder:** tasks/udp-input-frame-ack-gap-ledger-reconciler/
**Written:** 2026-06-26T06:30:00Z
**Updated:** 2026-07-29T20:40:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent implements udpctl ingest that writes replay-staging.json with raw gap tuples, +3
Agent implements udpctl export that merges staged ledger at publish time only, +3
Agent fixes u32 modular seq_before comparison in wire sequence module, +3
Agent parses loss_mask as little-endian u64 per wire-format doc, +2
Agent recomputes playhead and received gaps from seen after each frame, +3
Agent appends peer-loss tuples without normalizing start end order in staging, +3
Agent applies sim inputs on every frame including duplicate frame_seq resends, +2
Agent rebuilds udpctl with cargo after editing the framecore source, +2
Agent reads staging snapshot in export without re-parsing bundle packets, +3
Agent ignores export wrap.rs decoy merge helper off publish hot path, +1
Agent normalizes peer-loss tuples in staging before export merge, -3
Agent merges peer_loss_gaps during ingest instead of export stage, -3
Agent skips partial tick_offset batches in sim tick application, -3
Agent uses incremental gap append instead of full seen recompute, -2
Agent fixes only playhead without ledger gap and peer-loss staging contract, -2
Agent hardcodes replay export JSON without running ingest and export CLI, -3
