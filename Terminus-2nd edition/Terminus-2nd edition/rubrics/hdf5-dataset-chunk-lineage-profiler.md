# Platform rubric — hdf5-dataset-chunk-lineage-profiler

**Task folder:** tasks/hdf5-dataset-chunk-lineage-profiler/

Agent implements row-major chunk coordinate decoding from the chunk-traversal contract, +3
Agent merges parent_chain attributes with dataset attrs winning on key collisions, +3
Agent preserves catalog filter order when computing filter_chain_hash, +2
Agent counts masked cells using mask bitset semantics only, +2
Agent applies scale from effective attrs when emitting coord_labels, +2
Agent writes filter_chain_hash into every staging chunk record, +2
Agent sorts exported chunks by chunk_index before serializing lineage report, +1
Agent computes export_fingerprint as SHA-256 of compact datasets JSON only, +2
Agent honors TB3_BUNDLE override for hidden ingest bundles, +2
Agent produces byte-stable export output across repeated export runs, +1
Agent rebuilds chunkline with cargo before verifier pytest, +1
Agent wires ingest staging snapshot before export lineage emission, +2
Agent leaves decoy wrap module off the ingest and export hot path, +1
Agent reads only chunk-traversal doc and skips attribute-inheritance rules, -3
Agent sorts compression filter names alphabetically before hashing, -5
Agent applies parent attributes after dataset attrs overwriting child keys, -3
Agent inflates masked_cells using fill_value heuristics beyond mask bits, -2
Agent uses column-major linear chunk index mapping, -5
Agent omits filter_chain_hash from staging records, -3
Agent exports lineage report with unsorted chunk arrays, -2
