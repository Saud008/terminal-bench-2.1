package ingest

import "path/filepath"

// FragmentBasename returns the stable ingest source key.
func FragmentBasename(path string) string {
	return filepath.Base(path)
}
