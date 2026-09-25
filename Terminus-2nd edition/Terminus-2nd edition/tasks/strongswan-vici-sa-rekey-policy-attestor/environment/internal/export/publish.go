package export

import (
	"encoding/json"
	"os"

	"github.com/terminus/vicireplay/internal/model"
	"github.com/terminus/vicireplay/internal/staging"
)

func WriteReport(output string, violationCount int) error {
	raw, err := os.ReadFile(staging.ManifestPath())
	if err != nil {
		return err
	}
	var snap model.RekeySnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return err
	}
	activeSpi := snap.ActiveSpiOut
	if activeSpi == 0 {
		for i := len(snap.Verdicts) - 1; i >= 0; i-- {
			if snap.Verdicts[i].ActiveSpiOut > 0 {
				activeSpi = snap.Verdicts[i].ActiveSpiOut
				break
			}
		}
	}
	report := model.RekeyReport{
		ReportVersion:       1,
		TableSuffix:         snap.TableSuffix,
		TraceID:             snap.TraceID,
		InitiatorOffset:     snap.InitiatorOffset,
		Verdicts:            snap.Verdicts,
		ActiveSpiOut:        activeSpi,
		RekeyViolationCount: violationCount,
		ExportSource:        "staging_manifest",
	}
	out, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(output, out, 0o644)
}

func BuildStats(verdicts []model.EventVerdict) int {
	count := 0
	for _, v := range verdicts {
		if !v.Accepted && (v.RejectReason == "rekey_before_delete_ack" || v.RejectReason == "selector_narrowed" || v.RejectReason == "uid_reused" || v.RejectReason == "seq_not_monotonic") {
			count++
		}
	}
	return count
}

func PickActiveSpi(children map[int]model.ChildState) uint64 {
	var maxDeleted uint64
	for _, c := range children {
		if c.Deleted && c.SpiOut > maxDeleted {
			maxDeleted = c.SpiOut
		}
	}
	return maxDeleted
}
