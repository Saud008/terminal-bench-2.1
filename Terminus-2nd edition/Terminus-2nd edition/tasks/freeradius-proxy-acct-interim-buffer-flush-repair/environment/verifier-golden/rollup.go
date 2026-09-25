package export

import "github.com/terminus/radiusproxy/internal/model"

// RollupSessions aggregates export rows for legacy batch reports (not used by Publish).
func RollupSessions(sessions []model.SessionExport) (completed int, interim int) {
	for _, s := range sessions {
		if s.Status == "stopped" {
			completed++
		}
		if s.LastInterimTS > s.SessionStartTS && s.Status != "stopped" {
			interim++
		}
	}
	return completed, interim
}
