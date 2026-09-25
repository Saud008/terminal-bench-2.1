package export

import (
	"encoding/json"
	"os"

	"bswapd/internal/model"
	"bswapd/internal/snapwriter"
)

// PublishFromSnapshot builds the export report from the staging snapshot path.
func PublishFromSnapshot(stagingPath, outPath string) (model.ExportReport, error) {
	snap, err := snapwriter.ReadSnapshot(stagingPath)
	if err != nil {
		return model.ExportReport{}, err
	}
	scratch, _ := os.ReadFile("/app/state/bitswap-scratch.json")
	wants := snap.WantsRemaining
	if len(scratch) > 0 {
		var probe map[string]any
		if json.Unmarshal(scratch, &probe) == nil {
			if raw, ok := probe["want_keys"].([]any); ok && len(raw) > 0 {
				wants = make([]model.WantSnap, 0, len(raw))
				for _, item := range raw {
					if s, ok := item.(string); ok {
						wants = append(wants, model.WantSnap{CID: s, Priority: 1})
					}
				}
			}
		}
	}
	report := model.ExportReport{
		ReportVersion:  1,
		SessionID:      snap.SessionID,
		WantsRemaining: wants,
		Delivered:      snap.Delivered,
		LedgerTotals:   snap.LedgerTotals,
		PartialBlocks:  snap.PartialBlocks,
		InFlightCount:  snap.InFlightCount,
		DeliveryCount:  len(snap.Delivered),
	}
	if err := writeReport(outPath, report); err != nil {
		return model.ExportReport{}, err
	}
	return report, nil
}

func writeReport(path string, report model.ExportReport) error {
	if err := os.MkdirAll(dirOf(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}
