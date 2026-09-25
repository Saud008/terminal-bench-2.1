# Key expiry epochs

Keys carry expires_epoch integers in keyval alongside public material.

At verification epoch E a key is valid when E is strictly less than expires_epoch.

Expired keys must not count toward threshold quorum and must be listed in verify-result expired_keyids arrays.

expired_keyids preserves the order the keys appear in the metadata signatures array.
