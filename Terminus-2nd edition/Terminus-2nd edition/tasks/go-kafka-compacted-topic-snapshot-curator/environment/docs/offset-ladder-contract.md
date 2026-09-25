# Partition offset ordering

Within each partition, records are processed in strictly increasing offset order regardless of timestamp_ms.

Cross-partition ordering in staging follows global ingest order after segment merge.

Reconcile flags offset_regress when collapsed ordering violates offset monotonicity within a partition.
