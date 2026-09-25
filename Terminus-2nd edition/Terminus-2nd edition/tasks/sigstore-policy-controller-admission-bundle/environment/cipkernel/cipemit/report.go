// Package cipemit writes the sealed admission ledger to disk.
package cipemit

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/slsacip/cipkernel/ciptypes"
)

// WriteReport marshals report as indented JSON and writes it to path,
// creating parent directories as needed.
func WriteReport(report ciptypes.Report, path string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return fmt.Errorf("create output dir for %s: %w", path, err)
	}
	b, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal report: %w", err)
	}
	if err := os.WriteFile(path, b, 0o644); err != nil {
		return fmt.Errorf("write report %s: %w", path, err)
	}
	return nil
}
