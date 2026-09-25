# Offset bounds validation

For each tensor, offset end must be less than or equal to the payload section length. The payload section length equals file size minus eight minus header JSON length.

Reject tensors whose end offset would read past the payload slice even when the end is still inside the overall file due to header bytes.
