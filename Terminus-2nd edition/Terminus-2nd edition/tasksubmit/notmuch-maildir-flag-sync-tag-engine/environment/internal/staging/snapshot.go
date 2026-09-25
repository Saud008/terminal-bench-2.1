package staging

import (
	"encoding/json"
	"mailsync/internal/model"
	"os"
	"sort"
)

func WriteSnapshot(path string, snap model.Snapshot) error {
	sort.Slice(snap.Entries, func(i, j int) bool {
		return snap.Entries[i].MessageID < snap.Entries[j].MessageID
	})
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0644)
}

func ReadSnapshot(path string) (model.Snapshot, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return model.Snapshot{}, err
	}
	var snap model.Snapshot
	if err := json.Unmarshal(data, &snap); err != nil {
		return model.Snapshot{}, err
	}
	return snap, nil
}

// EntriesForIngest builds staging snapshot rows for ingest per staging-snapshot.md.
func EntriesForIngest(records []model.MailRecord) []model.SnapshotEntry {
	out := make([]model.SnapshotEntry, 0, len(records))
	for _, r := range records {
		out = append(out, model.SnapshotEntry{
			MessageID:      r.MessageID,
			MaildirRelpath: r.MaildirRelpath,
			Flags:          r.Flags,
			XKeywords:      nil,
			MtimeNs:        r.MtimeNs,
			Subject:        r.Subject,
		})
	}
	return out
}
