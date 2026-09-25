# Mask accounting

When mask_rel is present, masked_cells for each chunk equals the number of set bits in the mask for that chunk's cell span (product of chunk_dims). Each chunk evaluates the mask from bit index zero through (cell span minus one); do not offset by chunk index or global dataset position. Do not add fill_value comparisons or periodic padding to the count.

When mask_rel is absent, use masked_cells from the index sidecar row.

compression_totals.total_masked_cells sums masked_cells across all chunk records written to staging.
