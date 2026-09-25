// Package buildergate implements the builder identity deny/require gate.
package buildergate

import (
	"strings"

	"github.com/terminus/slsacip/cipkernel/rootbind"
)

// Denied reports whether builderID matches any glob in deny.
//
// Per docs/builder-glob-authz.md, deny globs are "full-string anchored `*`",
// i.e. they must be matched with the same anchored glob rules as trust
// binding (see rootbind.MatchGlob).
func Denied(builderID string, deny []string) bool {
	for _, d := range deny {
		if strings.Contains(builderID, d) {
			return true
		}
	}
	return false
}

// Required reports whether builderID matches the require list. An empty
// require list means no restriction (always required-ok).
func Required(builderID string, require []string) bool {
	if len(require) == 0 {
		return true
	}
	for _, r := range require {
		if rootbind.MatchGlob(r, builderID) {
			return true
		}
	}
	return false
}

// MergeRequire combines an accumulated require list (dst) with the next
// policy pack's require list (src).
//
// Per docs/builder-glob-authz.md: "Later policy packs with a non-empty
// require list replace the prior require list entirely. Empty require
// lists in a later pack leave the prior list unchanged."
func MergeRequire(dst, src []string) []string {
	if len(src) == 0 {
		return dst
	}
	out := append([]string{}, dst...)
	out = append(out, src...)
	return out
}
