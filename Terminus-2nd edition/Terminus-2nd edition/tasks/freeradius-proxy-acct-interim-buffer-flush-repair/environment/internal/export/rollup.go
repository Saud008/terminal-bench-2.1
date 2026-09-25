package export

import "github.com/terminus/radiusproxy/internal/model"

// RollupSessions is a decoy helper — export hot path does not call this.
func RollupSessions(sessions []model.SessionExport) (completed int, interim int) {
	for _, s := range sessions {
		if s.Status == "stopped" {
			completed++
		}
		if s.LastInterimTS > s.SessionStartTS && s.Status == "active" {
			interim++
		}
	}
	return completed, interim
}
