# Chunk grid validation

For each array, compute expected chunk slots as the product over dimensions of ceiling division:

```
slots = product( ceil(shape[d] / chunks[d]) )
```

`grid_topology_ok` is true when slots is greater than zero.

Present chunk keys must be a subset of the Cartesian product of valid chunk indices.

Chunk index `i.j` refers to chunk row `i` along dimension 0 and chunk column `j` along dimension 1.

Bundled fixtures name arrays `temperature` and `pressure`. The pressure manifest omits chunk key `1.1`. Hidden verifier manifests may add `humidity` with the same missing key pattern.
