package peerwant

import (
	"bswapd/internal/cid"
	"bswapd/internal/model"
)

func MergePeerWants(sess *model.Session, wants []model.Want) {
	for _, w := range wants {
		canon, err := cid.CanonicalKey(w.CID)
		if err != nil {
			continue
		}
		if sess.Canceled[canon] {
			continue
		}
		if ent, ok := sess.Wants[canon]; ok {
			if w.Priority > ent.Priority {
				ent.Priority = w.Priority
			}
			continue
		}
		sess.Wants[canon] = &model.WantEntry{
			DisplayCID: w.CID,
			Priority:   w.Priority,
			Canonical:  canon,
		}
	}
}

func ActiveWantKeys(sess *model.Session) []string {
	out := make([]string, 0, len(sess.Wants))
	for _, w := range sess.Wants {
		out = append(out, w.DisplayCID)
	}
	return out
}
