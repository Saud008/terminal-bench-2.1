package export

import (
	"encoding/json"
	"os"

	"bswapd/internal/traceplay"
	"bswapd/internal/model"
)

func BuildMetrics(sess *model.Session, cancelMerged bool) model.MetricsReport {
	head, pri, _ := traceplay.MetricsHead(sess)
	return model.MetricsReport{
		ReportVersion: 1,
		SessionID:     sess.Name,
		QueueHeadCID:  head,
		QueueHeadPri:  pri,
		CancelMerged:  cancelMerged,
	}
}

func WriteMetrics(path string, report model.MetricsReport) error {
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
