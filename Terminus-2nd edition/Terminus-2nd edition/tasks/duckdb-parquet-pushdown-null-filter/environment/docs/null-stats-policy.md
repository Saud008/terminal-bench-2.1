# Null stats policy

Column statistics may omit null_count when writers strip null summaries from footers. When null_count_omitted is true, pushdown must not treat null_count as zero proof of absence.

Row-group pruning for IS NULL predicates may skip a group only when stats_present is true, null_count_omitted is false, and null_count equals zero.

Timestamp min/max pruning must not drop a row group solely on min/max when null_count_omitted is true on that column. Conservative inclusion applies: read the group and evaluate rows.

Dictionary-encoded columns still expose a null_bitmap page. IS NULL matching requires honoring null_bitmap before dictionary filtering regardless of footer page_order listing.
