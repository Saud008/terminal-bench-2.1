package thread

import (
	"mailsync/internal/mailparse"
	"mailsync/internal/model"
	"sort"
)

func Bind(records []model.MailRecord, parsed map[string]mailparse.Parsed) ([]model.MailRecord, int) {
	parent := map[string]string{}
	ids := map[string]bool{}
	for _, r := range records {
		ids[r.MessageID] = true
		parent[r.MessageID] = r.MessageID
	}
	var find func(string) string
	find = func(x string) string {
		if parent[x] != x {
			parent[x] = find(parent[x])
		}
		return parent[x]
	}
	union := func(a, b string) {
		ra, rb := find(a), find(b)
		if ra == rb {
			return
		}
		if ra < rb {
			parent[rb] = ra
		} else {
			parent[ra] = rb
		}
	}
	for _, r := range records {
		p := parsed[r.MessageID]
		if p.InReplyTo != "" && ids[p.InReplyTo] {
			union(r.MessageID, p.InReplyTo)
		}
		for _, ref := range p.References {
			if ids[ref] {
				union(r.MessageID, ref)
			}
		}
	}
	roots := map[string]bool{}
	for id := range ids {
		roots[find(id)] = true
	}
	out := make([]model.MailRecord, len(records))
	copy(out, records)
	for i := range out {
		out[i].ThreadID = find(out[i].MessageID)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].MessageID < out[j].MessageID })
	return out, len(roots)
}
