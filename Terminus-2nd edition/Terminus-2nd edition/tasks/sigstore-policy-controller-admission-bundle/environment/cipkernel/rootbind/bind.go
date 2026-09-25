package rootbind

import (
	"strings"

	"github.com/terminus/slsacip/cipkernel/ciptypes"
)

// NormalizeDigest strips an optional "sha256:" prefix and lowercases the
// remaining hex, per docs/fulcio-root-bind.md. This helper is correct in
// the shipped baseline; it is the callers that must use it consistently.
func NormalizeDigest(s string) string {
	s = strings.TrimSpace(s)
	s = strings.ToLower(s)
	s = strings.TrimPrefix(s, "sha256:")
	return s
}

// Binds reports whether envelope e trust-binds root: both the root's
// issuer_glob and subject_glob must match e's issuer and subject
// respectively (see docs/fulcio-root-bind.md).
func Binds(root ciptypes.TrustRoot, e ciptypes.Envelope) bool {
	return MatchGlob(root.IssuerGlob, e.Issuer) && MatchGlob(root.SubjectGlob, e.Subject)
}
