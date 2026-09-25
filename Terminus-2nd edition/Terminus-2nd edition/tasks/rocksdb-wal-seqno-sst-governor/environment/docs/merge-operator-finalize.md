# Merge operator finalize

Merge operands carry operands (string encoded integers), partial_value, finalized, and seqno.

When finalized is false the export must not publish partial_value.

The exported value is the decimal string sum of operands parsed as signed 64-bit integers.

When finalized is true partial_value is ignored and operands are still summed.
