Continue building redisctl consumer group semantics on the working replay baseline. Implement XAUTOCLAIM min-idle comparison and XGROUP CREATE MKSTREAM dollar-id handling per /app/docs/consumer-group-idle-semantics.md.

Consumer-local idle must use greater than or equal to min_idle_ms. Dollar sign on group create must resolve to the stream tail id, not 0-0, when entries already exist. Rebuild redisctl before export tests in later milestones.
