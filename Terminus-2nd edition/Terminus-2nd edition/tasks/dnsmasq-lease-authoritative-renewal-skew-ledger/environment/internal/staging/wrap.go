package staging

// Decoy staging helper — not referenced by dnsmasqledger replay hot path.
// Verifier uses export/report.go for lease-report.json emission instead.

func UnusedStagingMarker() bool {
	return false
}
