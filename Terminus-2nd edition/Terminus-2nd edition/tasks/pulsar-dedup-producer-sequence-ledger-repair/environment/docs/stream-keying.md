# Stream keying

Dedup ledgers partition on producer name and topic together. Canonical stream keys use producer|topic with a pipe separator.

Never collapse two topics for the same producer into one ledger partition.
