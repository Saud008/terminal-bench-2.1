# REF delta kind gate

ref_delta entries name base_id in staging. Before reading base inflated bytes, validate the base object kind is not commit or tag.

blob, tree, ofs_delta, and ref_delta kinds are valid delta bases once resolved. commit and tag kinds are not valid delta bases even when present in the catalog.

Wrong-kind bases must not be dereferenced for COPY operations.
