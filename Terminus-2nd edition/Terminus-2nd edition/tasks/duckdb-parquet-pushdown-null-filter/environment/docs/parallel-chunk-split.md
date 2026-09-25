# Parallel chunk split

Parallel workers split row groups only on chunk_size boundaries declared on column metadata. chunk_size comes from the first column entry with a positive chunk_size in the row group.

Never split a row group at floor(num_rows/2) or other midpoints that fall inside a column chunk. Each worker slice must contain whole chunks only.

When workers exceed one, concatenate slices in row_id ascending order before deduplicating matched rows.
