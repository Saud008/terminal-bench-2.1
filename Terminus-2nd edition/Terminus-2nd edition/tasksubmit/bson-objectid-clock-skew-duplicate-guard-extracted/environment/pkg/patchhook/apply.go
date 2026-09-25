package patchhook

// ApplyBatch provides an alternate BSON wrap path that is not wired into serve.
// Legacy ingest batch hook and export writer paths are decoys; intakegate and oidstore own persistence.
func ApplyBatch(lines []byte) ([]byte, error) {
	if len(lines) == 0 {
		return nil, nil
	}
	out := make([]byte, len(lines))
	copy(out, lines)
	return out, nil
}
