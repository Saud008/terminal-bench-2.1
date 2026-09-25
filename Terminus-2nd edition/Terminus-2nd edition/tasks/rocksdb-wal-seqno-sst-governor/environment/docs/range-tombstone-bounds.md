# Range tombstone bounds

Range tombstones hide keys k in a column family when start less than or equal to k and k less than end.

The end key is exclusive (half-open interval).

A key equal to end remains visible unless hidden by a point tombstone with higher seqno.
