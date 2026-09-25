package export

import (
	"encoding/json"
	"os"

	"github.com/clickparts/chparts/internal/model"
	"github.com/clickparts/chparts/internal/staging"
)

func WriteReport(output string) error {
	raw, err := os.ReadFile(staging.SnapshotPath())
	if err != nil {
		return err
	}
	var snap model.Snapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return err
	}
	report := model.ExportReport{
		TableName: snap.TableName,
		MaxBlock:  snap.MaxBlock,
		RowCount:  len(snap.Rows),
		Rows:      snap.Rows,
		Parts:     OrderParts(snap.Parts),
	}
	out, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	return os.WriteFile(output, out, 0o644)
}
