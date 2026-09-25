package peerwant

import "wantplay/internal/model"

// MergePeerWants merges remote wants into the session want map.
func MergePeerWants(sess *model.Session, wants []model.Want) {
	for _, w := range wants {
		if _, ok := sess.Wants[w.CID]; !ok {
			sess.Wants[w.CID] = &model.WantEntry{
				DisplayCID: w.CID,
				Priority:   w.Priority,
				Canonical:  w.CID,
			}
		} else if w.Priority > sess.Wants[w.CID].Priority {
			sess.Wants[w.CID].Priority = w.Priority
		}
	}
}

// ActiveWantKeys returns sorted display CIDs still wanted.
func ActiveWantKeys(sess *model.Session) []string {
	out := make([]string, 0, len(sess.Wants))
	for k := range sess.Wants {
		out = append(out, k)
	}
	return out
}
