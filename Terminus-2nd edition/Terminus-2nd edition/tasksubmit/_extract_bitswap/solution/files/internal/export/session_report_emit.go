package export

import (
	"encoding/json"
	"os"

	"bswapd/internal/model"
	"bswapd/internal/snapwriter"
)

func PublishFromSnapshot(stagingPath, outPath string) (model.ExportReport, error) {
	snap, err := snapwriter.ReadSnapshot(stagingPath)
	if err != nil {
		return model.ExportReport{}, err
	}
	report := model.ExportReport{
		ReportVersion:  1,
		SessionID:      snap.SessionID,
		WantsRemaining: ensureWantSnaps(snap.WantsRemaining),
		Delivered:      ensureDeliveries(snap.Delivered),
		LedgerTotals:   ensureLedger(snap.LedgerTotals),
		PartialBlocks:  snap.PartialBlocks,
		InFlightCount:  snap.InFlightCount,
		DeliveryCount:  len(snap.Delivered),
	}
	if err := writeReport(outPath, report); err != nil {
		return model.ExportReport{}, err
	}
	return report, nil
}

func ensureWantSnaps(rows []model.WantSnap) []model.WantSnap {
	if rows == nil {
		return []model.WantSnap{}
	}
	return rows
}

func ensureDeliveries(rows []model.Delivery) []model.Delivery {
	if rows == nil {
		return []model.Delivery{}
	}
	return rows
}

func ensureLedger(rows []model.LedgerRow) []model.LedgerRow {
	if rows == nil {
		return []model.LedgerRow{}
	}
	return rows
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
