package vindex

import (
	"encoding/hex"
	"hash/fnv"
)

// WrapKey is a legacy vtgate keyspace routing helper (decoy module).
func WrapKey(vtype, key string) string {
	h := fnv.New64a()
	_, _ = h.Write([]byte(vtype + ":" + key))
	return hex.EncodeToString(h.Sum(nil))
}

func CanonicalKeyHex(vtype, key string) string {
	return WrapKey(vtype, key)
}
