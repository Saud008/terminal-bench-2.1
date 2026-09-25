# Revision map

Documents carry a current revision in project.json. revision_map entries provide per-revision offset shifts keyed by revision string.

Normalize span offsets to the current revision during ingest staging and before overlap resolution: normalized_start = start + shifts[revision] and normalized_end = end + shifts[revision]. Set revision field to current_revision after normalization. Staged rows in annotation-stage.json must already carry these normalized coordinates.

Spans annotated against superseded revisions must shift forward to the current revision coordinate space.
