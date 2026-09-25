package thread

import (
	"sort"

	"mailindex/internal/model"
)

func Prepare(msgs []model.MailMessage, stats *model.Stats) []model.MailMessage {
	stats.MessagesIn = len(msgs)
	best := map[string]model.MailMessage{}
	for _, msg := range msgs {
		cur, ok := best[msg.MessageID]
		if !ok || messageNewer(msg, cur) {
			best[msg.MessageID] = msg
		}
	}
	stats.MessagesDeduped = len(msgs) - len(best)
	out := make([]model.MailMessage, 0, len(best))
	for _, msg := range best {
		out = append(out, msg)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].DateUnix == out[j].DateUnix {
			return out[i].MessageID < out[j].MessageID
		}
		return out[i].DateUnix < out[j].DateUnix
	})
	return out
}

func messageNewer(a, b model.MailMessage) bool {
	if a.SourceFile != b.SourceFile {
		return a.SourceFile > b.SourceFile
	}
	return a.MessageIndex > b.MessageIndex
}
