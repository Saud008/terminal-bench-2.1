package export

import (
	"encoding/json"
	"mailsync/internal/model"
	"os"
	"sort"
)

func WriteReport(path string, rep model.Report) error {
	sort.Slice(rep.Messages, func(i, j int) bool {
		return rep.Messages[i].MessageID < rep.Messages[j].MessageID
	})
	for i := range rep.Messages {
		sort.Strings(rep.Messages[i].Tags)
	}
	raw, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0644)
}

func RecordsToReport(records []model.MailRecord, meta model.Report) model.Report {
	msgs := make([]model.ReportMessage, 0, len(records))
	for _, r := range records {
		tags := append([]string(nil), r.Tags...)
		sort.Strings(tags)
		msgs = append(msgs, model.ReportMessage{
			MessageID:      r.MessageID,
			ThreadID:       r.ThreadID,
			MaildirRelpath: r.MaildirRelpath,
			Flags:          r.Flags,
			Tags:           tags,
			KeywordsSource: r.KeywordsSource,
		})
	}
	meta.Messages = msgs
	meta.MessagesIndexed = len(msgs)
	meta.SyncVersion = 1
	return meta
}
