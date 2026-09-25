# Dtype and shape payload sizing

Element byte widths: F32 and I32 use four bytes, F16 and BF16 use two bytes, I64 uses eight bytes, U8 uses one byte.

Expected payload span equals the product of shape dimensions times element bytes. Mismatches between header data_offsets span and dtype shape sizing are scan validation failures.
