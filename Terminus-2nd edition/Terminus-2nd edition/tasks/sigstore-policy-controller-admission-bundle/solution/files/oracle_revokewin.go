// Package revokewin implements the revocation-window gate.
package revokewin

import (
	"time"

	"github.com/terminus/slsacip/cipkernel/ciptypes"
	"github.com/terminus/slsacip/cipkernel/rootbind"
)

// Hit reports whether digest (already normalized by the caller) is revoked
// at ts by any entry in revs.
//
// Per docs/revoke-halfopen.md, a revocation applies while ts lies in the
// half-open window [start, end) — end EXCLUSIVE.
func Hit(digest string, ts time.Time, revs []ciptypes.Revocation) bool {
	for _, r := range revs {
		if rootbind.NormalizeDigest(r.SubjectDigest) != digest {
			continue
		}
		if !ts.Before(r.Start) && ts.Before(r.End) {
			return true
		}
	}
	return false
}
