package export

import (
	"encoding/json"
	"os"

	"github.com/chronostack/metricrollup/internal/store"
)

// LegacyWriteReport is unused by vmrollup query; kept for migration tooling.
func LegacyWriteReport(dbPath, output string) error {
	st, err := store.Open(dbPath)
	if err != nil {
		return err
	}
	defer st.Close()
	stats, err := st.Stats()
	if err != nil {
		return err
	}
	raw, err := json.MarshalIndent(stats, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(output, raw, 0644)
}
