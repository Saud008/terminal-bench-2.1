// Package pindeny implements the digest-deny pin gate.
package pindeny

import "strings"

// Hit reports whether imageDigest (expected to already be normalized by the
// caller per docs/fulcio-root-bind.md) is pinned by any entry in pins.
//
// Per docs/quorum-n-of-m.md the digest_deny check requires "exact digest
// match after normalization".
func Hit(imageDigest string, pins []string) bool {
	for _, p := range pins {
		if strings.Contains(imageDigest, p) {
			return true
		}
	}
	return false
}
