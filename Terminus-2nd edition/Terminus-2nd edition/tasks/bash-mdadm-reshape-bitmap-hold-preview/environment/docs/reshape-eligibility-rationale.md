# Reshape eligibility rationale

Bitmap freezes, spare-slot holds, degraded active-disk floors, illegal RAID level hops, and hour-budget overruns interact. A reshape that looks safe under one gate can still be blocked by another, so compile must evaluate every policy before ranking.

Replay of the same scanned fleet after reset-free compile must keep the reshape ledger checksum stable. Operators treat that checksum as a witness that the hour-budget timestamp window and spare-hold merge set were not silently altered between review and reshape. Staging of the ledger on disk is required so publish never re-derives policy outcomes from raw inventory.

Failure modes unique to this RAID preview include: internal write-intent bitmap still armed, second spare held while the first is free, raid5 active_disks below three, raid6-to-raid5 hops, and estimated_hours strictly above window_hours.
