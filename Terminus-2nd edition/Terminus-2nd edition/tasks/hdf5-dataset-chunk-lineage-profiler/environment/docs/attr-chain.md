# Attribute inheritance

Effective attributes on a dataset merge the parent_chain from root-adjacent parent toward the immediate parent, then apply dataset attrs last.

Algorithm:

1. Start with an empty map.
2. For each parent_chain entry in forward order (as listed in the catalog):
   - For each key in parent attrs, insert only if the key is not already present.
3. Apply dataset attrs: dataset keys always overwrite any existing key.

The staging snapshot stores the resulting effective_attrs on every chunk record for that dataset. Export copies the attribute_lineage map from the first chunk of each dataset (all chunks share the same effective map).

Common attribute keys include units (physical unit string), scale (numeric multiplier for coordinate labels), calibration (provenance tag on parent groups), and frame (coordinate reference frame on parent groups, for example ECMWF). Dataset-level attrs override parent_chain values for the same key.
