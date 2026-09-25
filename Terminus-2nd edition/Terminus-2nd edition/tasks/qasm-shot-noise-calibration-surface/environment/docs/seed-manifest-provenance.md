# Seed manifest provenance

The provenance chain binds calibration lineage into the envelope ledger before export digest computation.

Collect these strings into a chain list: every entry from manifest calibration_ids in file order, then experiment_id, then selected_matrix_id from matrix selection.

Sort the chain list alphabetically ascending before binding. Sorting is mandatory even when calibration_ids already appear ordered.

The sorted chain is stored in ledger provenance.chain. The provenance digest field is the lowercase hex SHA256 of the UTF-8 JSON array of the sorted chain with no whitespace.

Export digest computation must include the full provenance object including chain and digest fields.
