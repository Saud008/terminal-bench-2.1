// Package decoy hosts legacy shim helpers that are not on the dnsplugd answer hot path.
// The verifier does not exercise this package.
package decoy

// LegacyShimPlaceholder documents an unused helper kept for layout parity.
func LegacyShimPlaceholder() bool { return false }
