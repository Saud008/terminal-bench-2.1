package thread

import (
	"sort"

	"mailindex/internal/model"
)

func AssignThreads(msgs []model.MailMessage, stats *model.Stats) []model.IndexedMessage {
	ids := make(map[string]model.MailMessage, len(msgs))
	for _, msg := range msgs {
		ids[msg.MessageID] = msg
	}
	parent := make(map[string]string, len(msgs))
	for id := range ids {
		parent[id] = id
	}
	var find func(string) string
	find = func(x string) string {
		if parent[x] != x {
			parent[x] = find(parent[x])
		}
		return parent[x]
	}
	union := func(a, b string) {
		ra := find(a)
		rb := find(b)
		if ra == rb {
			return
		}
		if ra < rb {
			parent[rb] = ra
			return
		}
		parent[ra] = rb
	}
	LinkMessages(msgs, ids, union)

	components := map[string][]model.MailMessage{}
	for id := range ids {
		rootKey := find(id)
		components[rootKey] = append(components[rootKey], ids[id])
	}
	rootForComponent := PickThreadRoots(components)
	stats.ThreadsResolved = len(rootForComponent)

	out := make([]model.IndexedMessage, 0, len(msgs))
	for _, msg := range msgs {
		comp := find(msg.MessageID)
		threadRoot := rootForComponent[comp]
		out = append(out, model.IndexedMessage{
			MessageID:    msg.MessageID,
			ThreadRootID: threadRoot,
			DateUnix:     msg.DateUnix,
			Subject:      msg.Subject,
			IsRoot:       msg.MessageID == threadRoot,
		})
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].DateUnix == out[j].DateUnix {
			return out[i].MessageID < out[j].MessageID
		}
		return out[i].DateUnix < out[j].DateUnix
	})
	return out
}
