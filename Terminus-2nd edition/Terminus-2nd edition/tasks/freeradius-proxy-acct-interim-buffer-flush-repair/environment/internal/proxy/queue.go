package proxy

import (
	"sort"

	"github.com/terminus/radiusproxy/internal/model"
)

func Enqueue(state *model.ProxyState, entry model.FlushEntry) {
	state.FlushQueue = append(state.FlushQueue, entry)
}

func FlushDue(state *model.ProxyState, nowTS int64, stats *model.Stats) []model.FlushEntry {
	var due []model.FlushEntry
	remain := make([]model.FlushEntry, 0, len(state.FlushQueue))
	for _, e := range state.FlushQueue {
		sess := findSession(state, e.NASID, e.AcctSessionID)
		if sess == nil {
			remain = append(remain, e)
			continue
		}
		if nowTS-sess.LastFlushTS >= int64(sess.InterimIntervalSec) {
			due = append(due, e)
		} else {
			remain = append(remain, e)
		}
	}
	sort.Slice(due, func(i, j int) bool {
		return due[i].Seq < due[j].Seq
	})
	state.FlushQueue = remain
	if len(due) > 0 {
		stats.FlushBatches++
		stats.InterimFlushed += len(due)
		for i := range due {
			if sess := findSession(state, due[i].NASID, due[i].AcctSessionID); sess != nil {
				sess.LastFlushTS = nowTS
			}
		}
	}
	return due
}

// FlushPendingForStop drains queued interim entries for a session being stopped.
func FlushPendingForStop(state *model.ProxyState, sess *model.SessionState, nowTS int64, stats *model.Stats) []model.FlushEntry {
	return nil
}

func findSession(state *model.ProxyState, nasID, acctSessionID string) *model.SessionState {
	for _, s := range state.Sessions {
		if s.NASID == nasID && s.AcctSessionID == acctSessionID && s.Status == "active" {
			return s
		}
	}
	return nil
}
