# Delta chain ordering

When multiple objects share a pack, resolve inflated bytes in dependency order:

1. Compute chain_depth for each object as the number of delta hops to a non-delta root (blob or tree).
2. Resolve all objects with lower chain_depth before any object with higher chain_depth.
3. When depths tie, use catalog_order ascending.

Depth-first leaf-first walks that visit a delta before its ultimate base are incorrect. Longest-base-first means bases and shallow chains are fully inflated before deeper dependents consume them.

The export chain_depth field reports the delta hop count from staging metadata after correct resolution.
