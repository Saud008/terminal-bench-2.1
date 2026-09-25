package journal

import (
	"dnsmasqledger/internal/model"
)

func Append(cat *model.Catalog, ev model.ReplayEvent, ok bool) {
	cat.Journal = append(cat.Journal, model.JournalEntry{
		Seq: ev.Seq,
		Op:  ev.Op,
		OK:  ok,
		At:  cat.NowSec,
	})
}

func Tail(cat *model.Catalog, n int) []model.JournalEntry {
	if n <= 0 || len(cat.Journal) == 0 {
		return nil
	}
	if len(cat.Journal) <= n {
		out := make([]model.JournalEntry, len(cat.Journal))
		copy(out, cat.Journal)
		return out
	}
	out := make([]model.JournalEntry, n)
	copy(out, cat.Journal[len(cat.Journal)-n:])
	return out
}
