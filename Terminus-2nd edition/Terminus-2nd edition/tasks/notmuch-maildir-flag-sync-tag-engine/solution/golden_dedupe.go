package thread

import (
	"mailsync/internal/model"
	"sort"
)

// Dedupe collapses duplicate Message-ID rows per message-id-dedupe.md.
func Dedupe(records []model.MailRecord) ([]model.MailRecord, int) {
	best := map[string]model.MailRecord{}
	for _, r := range records {
		cur, ok := best[r.MessageID]
		if !ok || Better(r, cur) {
			best[r.MessageID] = r
		}
	}
	out := make([]model.MailRecord, 0, len(best))
	for _, r := range best {
		out = append(out, r)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].MessageID < out[j].MessageID })
	return out, len(records) - len(out)
}

func folderRank(relpath string) int {
	if len(relpath) >= 4 && relpath[:4] == "cur/" {
		return 2
	}
	if len(relpath) >= 4 && relpath[:4] == "new/" {
		return 1
	}
	return 0
}

func Better(a, b model.MailRecord) bool {
	if a.MtimeNs != b.MtimeNs {
		return a.MtimeNs > b.MtimeNs
	}
	ra, rb := folderRank(a.MaildirRelpath), folderRank(b.MaildirRelpath)
	if ra != rb {
		return ra > rb
	}
	return a.MaildirRelpath > b.MaildirRelpath
}
