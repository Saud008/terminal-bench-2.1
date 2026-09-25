package staging

import "mailsync/internal/model"

// ValidateSnapshot checks snapshot shape for legacy ingest callers (decoy — not on sync hot path).
func ValidateSnapshot(snap model.Snapshot) bool {
	if snap.SyncVersion < 1 {
		return false
	}
	for _, e := range snap.Entries {
		if e.MessageID == "" {
			return false
		}
	}
	return len(snap.Entries) >= 0
}
