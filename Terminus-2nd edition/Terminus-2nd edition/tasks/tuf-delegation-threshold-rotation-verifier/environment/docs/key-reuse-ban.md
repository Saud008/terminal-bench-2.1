# Key reuse ban

Root-role keyids declared in root signed roles.root.keyids must never count toward the targets metadata signature threshold.

If a signature on targets or snapshot metadata uses a root-role keyid, that signature is ignored for quorum and recorded in verify-result reuse_violations regardless of whether the keyid is listed in the metadata role keyids.

This ban applies even when the key is still temporally valid.
