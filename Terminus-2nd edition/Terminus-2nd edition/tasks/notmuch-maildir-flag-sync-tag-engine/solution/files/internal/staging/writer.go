package staging

import "mailsync/internal/model"

func BuildSnapshot(root, db string, epoch, filesSeen, in, skipped int, records []model.MailRecord) model.Snapshot {
	return model.Snapshot{
		SyncVersion:      1,
		StagingEpoch:     epoch,
		MaildirRoot:      root,
		DBPath:           db,
		MaildirFilesSeen: filesSeen,
		MessagesIn:       in,
		MessagesSkipped:  skipped,
		Entries:          EntriesForIngest(records),
	}
}
