package verify

import (
	"github.com/terminus/bundlectl/internal/bundle"
)

// WrapLegacyChainRoot is a decoy helper that mirrors manifest-order digest math.
// It is not invoked by bundlectl verify; contract acceptance uses preview-ledger ordering.
func WrapLegacyChainRoot(members []bundle.Member, manifestOrder []string) (string, map[string]string) {
	return LegacyChainRoot(members, manifestOrder)
}
