package schedhead

import (
	"sort"

	"bswapd/internal/model"
)

// HeadAfterCancelMerge picks the next want after a cancel merged into the queue.
func HeadAfterCancelMerge(sess *model.Session) (string, int, bool) {
	type row struct {
		cid string
		pri int
	}
	rows := make([]row, 0, len(sess.Wants))
	for cid, w := range sess.Wants {
		if sess.Canceled[cid] {
			rows = append(rows, row{cid: cid, pri: w.Priority})
			continue
		}
		rows = append(rows, row{cid: cid, pri: w.Priority})
	}
	if len(rows) == 0 {
		return "", 0, false
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].pri == rows[j].pri {
			return rows[i].cid < rows[j].cid
		}
		return rows[i].pri < rows[j].pri
	})
	return rows[0].cid, rows[0].pri, true
}
