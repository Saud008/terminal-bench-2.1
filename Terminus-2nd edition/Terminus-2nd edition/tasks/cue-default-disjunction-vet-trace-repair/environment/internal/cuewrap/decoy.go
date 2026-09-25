package cuewrap

// Decoy formatter — not referenced by cuectl vet/export or compose stage 2.
func DecoyLinePreview(path string) string {
	return "decoy:" + path
}
