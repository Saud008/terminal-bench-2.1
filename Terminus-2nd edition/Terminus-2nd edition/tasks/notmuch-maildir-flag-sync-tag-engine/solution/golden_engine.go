package syncengine

import (
	"mailsync/internal/export"
	"mailsync/internal/maildir"
	"mailsync/internal/mailparse"
	"mailsync/internal/model"
	"mailsync/internal/staging"
	"mailsync/internal/store"
	"mailsync/internal/tags"
	"mailsync/internal/thread"
	"os"
	"path/filepath"
)

type Result struct {
	Report model.Report
}

func Ingest(maildirRoot, dbPath string) error {
	res, err := scan(maildirRoot, dbPath)
	if err != nil {
		return err
	}
	db, err := store.Open(dbPath)
	if err != nil {
		return err
	}
	defer db.Close()
	epoch, _ := store.GetStagingEpoch(db)
	snap := staging.BuildSnapshot(maildirRoot, dbPath, epoch, res.filesSeen, res.messagesIn, res.skipped, res.records)
	return staging.WriteSnapshot(model.SnapshotPath, snap)
}

func Sync(maildirRoot, dbPath, reportPath string) error {
	res, err := scan(maildirRoot, dbPath)
	if err != nil {
		return err
	}
	db, err := store.Open(dbPath)
	if err != nil {
		return err
	}
	defer db.Close()
	epoch, _ := store.GetStagingEpoch(db)
	snap := staging.BuildSnapshot(maildirRoot, dbPath, epoch, res.filesSeen, res.messagesIn, res.skipped, res.records)
	if err := staging.WriteSnapshot(model.SnapshotPath, snap); err != nil {
		return err
	}
	meta := model.Report{
		MaildirFilesSeen: res.filesSeen,
		MessagesSkipped:  res.skipped,
		DuplicatesMerged: res.duplicates,
		ThreadsResolved:  res.threads,
	}
	if err := export.SyncPublish(db, maildirRoot, res.records, reportPath, meta); err != nil {
		return err
	}
	epoch, _ = store.GetStagingEpoch(db)
	snap = staging.BuildSnapshot(maildirRoot, dbPath, epoch, res.filesSeen, res.messagesIn, res.skipped, res.records)
	return staging.WriteSnapshot(model.SnapshotPath, snap)
}

func Publish(dbPath, reportPath string) error {
	snap, err := staging.ReadSnapshot(model.SnapshotPath)
	if err != nil {
		return err
	}
	db, err := store.Open(dbPath)
	if err != nil {
		return err
	}
	defer db.Close()
	meta := model.Report{
		StagingEpoch:     snap.StagingEpoch,
		MaildirFilesSeen: snap.MaildirFilesSeen,
		MessagesSkipped:  snap.MessagesSkipped,
		DuplicatesMerged: snap.MessagesIn - len(snap.Entries),
	}
	if meta.DuplicatesMerged < 0 {
		meta.DuplicatesMerged = 0
	}
	records, err := store.ListMessages(db)
	if err != nil {
		return err
	}
	records = overlaySnapshotKeywords(records, snap)
	meta.ThreadsResolved = countThreads(records)
	meta.TagWrites = len(records)
	meta.FlagRenames = 0
	rep := export.RecordsToReport(records, meta)
	rep.CommitBeforeRename = true
	return export.WriteReport(reportPath, rep)
}

func overlaySnapshotKeywords(records []model.MailRecord, snap model.Snapshot) []model.MailRecord {
	kwByID := map[string][]string{}
	for _, e := range snap.Entries {
		if len(e.XKeywords) > 0 {
			kwByID[e.MessageID] = append([]string(nil), e.XKeywords...)
		}
	}
	out := make([]model.MailRecord, len(records))
	copy(out, records)
	for i := range out {
		xkw, ok := kwByID[out[i].MessageID]
		if !ok || len(xkw) == 0 {
			continue
		}
		ft := tags.FlagTags(out[i].Flags)
		merged, src := tags.Merge(xkw, ft, out[i].Tags)
		out[i].Tags = merged
		out[i].KeywordsSource = src
	}
	return out
}

func countThreads(records []model.MailRecord) int {
	roots := map[string]bool{}
	for _, r := range records {
		roots[r.ThreadID] = true
	}
	return len(roots)
}

type scanResult struct {
	records    []model.MailRecord
	filesSeen  int
	messagesIn int
	skipped    int
	duplicates int
	threads    int
}

func scan(maildirRoot, dbPath string) (scanResult, error) {
	files, err := maildir.Scan(maildirRoot)
	if err != nil {
		return scanResult{}, err
	}
	var raw []model.MailRecord
	parsed := map[string]mailparse.Parsed{}
	skipped := 0
	for _, f := range files {
		path := filepath.Join(maildirRoot, filepath.FromSlash(f.Relpath))
		data, err := os.ReadFile(path)
		if err != nil {
			skipped++
			continue
		}
		p, ok := mailparse.ParseMessage(data)
		if !ok {
			skipped++
			continue
		}
		_, flagRaw := maildir.SplitFlags(f.Relpath)
		flags := maildir.NormalizeFlags(flagRaw)
		rec := model.MailRecord{
			MessageID:      p.MessageID,
			MaildirRelpath: f.Relpath,
			Flags:          flags,
			MtimeNs:        f.MtimeNs,
			Subject:        p.Subject,
			XKeywords:      p.XKeywords,
		}
		raw = append(raw, rec)
		parsed[p.MessageID] = p
	}
	db, _ := store.Open(dbPath)
	if db != nil {
		defer db.Close()
		for i := range raw {
			dbTags, _ := store.LoadDBTags(db, raw[i].MessageID)
			ft := tags.FlagTags(raw[i].Flags)
			merged, src := tags.Merge(raw[i].XKeywords, ft, dbTags)
			raw[i].Tags = merged
			raw[i].KeywordsSource = src
		}
	} else {
		for i := range raw {
			ft := tags.FlagTags(raw[i].Flags)
			merged, src := tags.Merge(raw[i].XKeywords, ft, nil)
			raw[i].Tags = merged
			raw[i].KeywordsSource = src
		}
	}
	deduped, dup := thread.Dedupe(raw)
	bound, threadCount := thread.Bind(deduped, parsed)
	return scanResult{
		records:    bound,
		filesSeen:  len(files),
		messagesIn: len(raw),
		skipped:    skipped,
		duplicates: dup,
		threads:    threadCount,
	}, nil
}
