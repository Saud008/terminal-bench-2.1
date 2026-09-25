# Page read order

Logical decode order for nullable dictionary columns is always null_bitmap, then dictionary, then data regardless of how page_order appears in catalog metadata.

The page reader must apply null_bitmap semantics before dictionary membership filters when evaluating IS NULL or IS NOT NULL predicates.

Data pages are pass-through once null and dictionary layers are resolved.
