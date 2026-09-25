package export

import (
	"database/sql"
	"mailsync/internal/maildir"
	"mailsync/internal/model"
	"mailsync/internal/store"
	"os"
	"path/filepath"
)

type RenamePlan struct {
	OldRel string
	NewRel string
}

func ApplyRenames(root string, plans []RenamePlan) (int, error) {
	count := 0
	for _, p := range plans {
		oldPath := filepath.Join(root, filepath.FromSlash(p.OldRel))
		newPath := filepath.Join(root, filepath.FromSlash(p.NewRel))
		if oldPath == newPath {
			continue
		}
		if err := os.Rename(oldPath, newPath); err != nil {
			return count, err
		}
		count++
	}
	return count, nil
}

// SyncPublish applies maildir renames and persists rows per sync-transaction-order.md.
func SyncPublish(db *sql.DB, root string, records []model.MailRecord, reportPath string, meta model.Report) error {
	plans := buildRenamePlans(records)
	renames, err := ApplyRenames(root, plans)
	if err != nil {
		return err
	}
	meta.FlagRenames = renames
	_, err = store.UpsertMessages(db, records)
	if err != nil {
		return err
	}
	meta.CommitBeforeRename = false
	meta.TagWrites = len(records)
	rep := RecordsToReport(records, meta)
	return WriteReport(reportPath, rep)
}

func buildRenamePlans(records []model.MailRecord) []RenamePlan {
	var plans []RenamePlan
	for _, r := range records {
		_, flags := maildir.SplitFlags(r.MaildirRelpath)
		want := maildir.FlagsFromTags(r.Tags)
		if flags == want {
			continue
		}
		folder := filepath.Dir(r.MaildirRelpath)
		base, _ := maildir.SplitFlags(filepath.Base(r.MaildirRelpath))
		newRel := maildir.JoinRelpath(folder, base, want)
		plans = append(plans, RenamePlan{OldRel: r.MaildirRelpath, NewRel: newRel})
	}
	return plans
}

func PublishFromDB(db *sql.DB, reportPath string, meta model.Report) error {
	records, err := store.ListMessages(db)
	if err != nil {
		return err
	}
	rep := RecordsToReport(records, meta)
	rep.CommitBeforeRename = true
	return WriteReport(reportPath, rep)
}
