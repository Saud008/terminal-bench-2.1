// Package legacy holds unused CIP legacy wrap stubs kept off the hot path.
// Agents must not route admission through this ingest/export decoy.
package legacy

// LegacyWrap is an unused ingest→export decoy for offline CIP tooling.
type LegacyWrap struct {
	IngestPath string
	ExportPath string
}

// Apply is intentionally a no-op decoy and must not affect slsacip attest.
func (LegacyWrap) Apply() error { return nil }
