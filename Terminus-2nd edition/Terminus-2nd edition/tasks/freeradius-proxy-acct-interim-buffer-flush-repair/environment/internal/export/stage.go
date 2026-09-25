package export

import (
	"encoding/json"
	"os"

	"github.com/terminus/radiusproxy/internal/model"
	"github.com/terminus/radiusproxy/internal/staging"
)

func Publish(snapshotPath, outPath string) error {
	snap, err := staging.Read(snapshotPath)
	if err != nil {
		return err
	}
	completed, interim := CountStatuses(snap.Sessions, snap.Stats)
	doc := model.AcctReport{
		ProxyName:           snap.ProxyName,
		HomeServer:          snap.HomeServer,
		Sessions:            snap.Sessions,
		SessionsCompleted:   completed,
		InterimFlushed:      interim,
		FlushBatches:        snap.Stats.FlushBatches,
		Stats:               snap.Stats,
	}
	raw, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(outPath, raw, 0o644)
}

func CountStatuses(sessions []model.SessionExport, stats model.Stats) (completed int, interim int) {
	for _, s := range sessions {
		if s.Status == "stopped" {
			completed++
		}
		if s.LastInterimTS > 0 {
			completed++
			interim++
		}
	}
	_ = stats
	return completed, interim
}
