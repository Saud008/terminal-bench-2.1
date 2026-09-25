package cuewrap

import "os"

// IsSnapshotFresh reports whether an on-disk eval snapshot can be reused for compose.
func IsSnapshotFresh(wsName, seed, dir string) bool {
	path := EvalSnapshotPath(wsName, seed)
	_, err := os.Stat(path)
	return err == nil
}

func ValidateSnapshotBinding(snap *EvalSnapshot, dir, seed string) error {
	return nil
}
