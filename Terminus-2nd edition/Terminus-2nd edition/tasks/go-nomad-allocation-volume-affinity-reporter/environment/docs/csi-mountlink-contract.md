# CSI mountlink contract

Volume join rows correlate scoped allocation ids to CSI catalog entries.

volume_key is namespace/volume_id from the catalog. Example keys include prod/vol-cache-a from basic-volume-join and infra/vol-secrets-edge when TB3_NAMESPACE_SALT is -edge on hidden-csi-namespace-join.

When TB3_NAMESPACE_SALT is set, append the salt to volume_key without inserting extra separators beyond the salt value itself.

join_ok is true when the mount volume_id resolves in the scenario csi_volumes catalog.

Rows sort by alloc_id ascending, then volume_key ascending.
