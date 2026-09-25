package bundle

func IngestPreview(bundleDir string, members []Member, manifestOrder []string) error {
	return WritePreviewLedger(bundleDir, members, manifestOrder)
}
