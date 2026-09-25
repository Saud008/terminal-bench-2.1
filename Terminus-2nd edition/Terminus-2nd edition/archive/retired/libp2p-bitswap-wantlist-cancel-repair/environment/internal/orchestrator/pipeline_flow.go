package orchestrator

import (
	"bswapd/internal/export"
	"bswapd/internal/traceplay"
	"bswapd/internal/model"
	"bswapd/internal/snapwriter"
)

func RunIngestStagingExport(logPath, sessionName, stagingPath, exportPath string) (*model.Session, error) {
	sess, err := traceplay.ReplayFile(logPath, sessionName)
	if err != nil {
		return nil, err
	}
	_ = snapwriter.ScratchManifest(sess)
	snap := snapwriter.BuildSnapshot(sess)
	if err := snapwriter.WriteSnapshot(stagingPath, snap); err != nil {
		return nil, err
	}
	if _, err := export.PublishFromSnapshot(stagingPath, exportPath); err != nil {
		return nil, err
	}
	return sess, nil
}

func RunMetricsReplay(logPath, sessionName, outPath string) error {
	sess, err := traceplay.ReplayFile(logPath, sessionName)
	if err != nil {
		return err
	}
	report := export.BuildMetrics(sess, true)
	return export.WriteMetrics(outPath, report)
}
