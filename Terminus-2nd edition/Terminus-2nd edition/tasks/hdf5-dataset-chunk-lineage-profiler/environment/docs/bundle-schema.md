# S5 catalog schema

Each bundle directory contains:

- catalog.s5cat — UTF-8 JSON catalog (see fields below)
- indexes/<dataset_path_with_slashes_as_underscores>.s5idx — binary chunk index per dataset
- Optional mask files referenced by mask_rel on each dataset

Catalog JSON fields:

- version: must be 1
- root: logical root path string (for example /)
- datasets: array of dataset objects

Each dataset object:

- path: absolute-style dataset path (for example /obs/temp)
- dims: full dataset dimension lengths as unsigned integers
- chunk_dims: chunk shape per dimension
- filters: ordered list of compression filter names (order matters for identity)
- fill_value: sentinel value for unmasked holes (not counted as masked by itself)
- mask_rel: optional relative path to a mask file inside the bundle
- attrs: dataset-local attributes as string-keyed JSON values
- parent_chain: ordered list from root-adjacent group down to immediate parent; each entry has path and attrs

Index sidecar binary layout (little-endian):

- 4 bytes magic S5IX
- uint32 ndims
- uint32 chunk_count
- repeated chunk_count times:
  - ndims * uint64 origin coordinates (byte offset per dimension in the dataset)
  - uint32 filter_chain_id (informational; lineage uses hash of filter names)
  - uint32 payload_bytes
  - uint32 masked_cells (authoritative when no mask file is present)

Mask files are raw bytes; bit i set means cell i within the chunk is masked (missing). Bits are packed little-endian within each byte.
