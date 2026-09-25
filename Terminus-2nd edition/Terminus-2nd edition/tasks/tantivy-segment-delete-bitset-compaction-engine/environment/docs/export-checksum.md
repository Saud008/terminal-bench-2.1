# Export checksum

The merge-checksum.txt digest is SHA-256 hex over compact JSON bytes of the stats object with merge_pass forced to zero and norm values as u8.

Do not hash pretty-printed stats file text or the on-disk segment JSON inputs.
