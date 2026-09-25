package bundle

// IngestPreview stages manifest members into the import-preview ledger before
// export-facing digest chain math runs during verify.
func IngestPreview(bundleDir string, members []Member, manifestOrder []string) error {
	return WritePreviewLedger(bundleDir, members, manifestOrder)
}
