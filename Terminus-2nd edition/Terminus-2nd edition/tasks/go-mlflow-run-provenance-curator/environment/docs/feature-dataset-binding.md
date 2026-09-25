# Dataset version binding

Each training run may pin feature datasets by name and version_hash. Manifests in the scenario supply authoritative version_hash and row_count per dataset name for eval reproducibility.

A binding is valid only when the pin version_hash equals the manifest version_hash for that dataset name after any TB3_MANIFEST_SALT suffix required by the active environment.

dataset_bindings in summary lists one row per pin on the focus run with fields: name, version_hash, row_count, bind_ok.

binding_ok in summary is true when every pin on the focus run is valid and at least one pin exists.
