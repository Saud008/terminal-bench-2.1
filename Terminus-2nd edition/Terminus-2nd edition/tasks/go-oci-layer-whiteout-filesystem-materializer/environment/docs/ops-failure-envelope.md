# Ops failure envelope — layerfuse filesystem control plane

Supply-chain auditors use layerfuse to prove which paths survive an ordered OCI tar stack after AUFS whiteout and opaque hold gates fire. The failure envelope is partial merge: ops passes that align only path cleaning or only export hashing still emit atlases that disagree with hidden fixture stacks mounted at runtime under /opt/verifier-fixtures/oci-layers.
