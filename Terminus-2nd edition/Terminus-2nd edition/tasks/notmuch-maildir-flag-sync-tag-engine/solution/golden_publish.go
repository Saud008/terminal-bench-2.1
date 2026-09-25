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

func SyncPublish(db *sql.DB, root string, records []model.MailRecord, reportPath string, meta model.Report) error {
	plans := buildRenamePlans(records)
	planByOld := map[string]string{}
	for _, p := range plans {
		planByOld[p.OldRel] = p.NewRel
	}
	for i := range records {
		want := maildir.FlagsFromTags(records[i].Tags)
		records[i].Flags = want
		if newRel, ok := planByOld[records[i].MaildirRelpath]; ok {
			records[i].MaildirRelpath = newRel
		}
	}
	if err := store.SetPhase(db, "committing"); err != nil {
		return err
	}
	_, err := store.UpsertMessages(db, records)
	if err != nil {
		return err
	}
	epoch, err := store.BumpStagingEpoch(db)
	if err != nil {
		return err
	}
	if err := store.SetPhase(db, "committed"); err != nil {
		return err
	}
	meta.StagingEpoch = epoch
	meta.CommitBeforeRename = true
	renames, err := ApplyRenames(root, plans)
	if err != nil {
		return err
	}
	meta.FlagRenames = renames
	meta.TagWrites = len(records)
	rep := RecordsToReport(records, meta)
	return WriteReport(reportPath, rep)
}

func buildRenamePlans(records []model.MailRecord) []RenamePlan {
	var plans []RenamePlan
	for _, r := range records {
		_, flags := maildir.SplitFlags(r.MaildirRelpath)
		want := maildir.FlagsFromTags(r.Tags)
		if maildir.NormalizeFlags(flags) == want {
			continue
		}
		folder := filepath.Dir(r.MaildirRelpath)
		base, _ := maildir.SplitFlags(filepath.Base(r.MaildirRelpath))
		newRel := maildir.JoinRelpath(folder, base, want)
		if r.MaildirRelpath == newRel {
			continue
		}
		plans = append(plans, RenamePlan{OldRel: r.MaildirRelpath, NewRel: newRel})
	}
	return plans
}

func PublishFromDB(db *sql.DB, reportPath string, meta model.Report) error {
	records, err := store.ListMessages(db)
	if err != nil {
		return err
	}
	meta.TagWrites = len(records)
	rep := RecordsToReport(records, meta)
	rep.CommitBeforeRename = true
	return WriteReport(reportPath, rep)
}
