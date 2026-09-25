package replay

import (
	"sort"

	"dnsmasqledger/internal/checkpoint"
	"dnsmasqledger/internal/journal"
	"dnsmasqledger/internal/lease"
	"dnsmasqledger/internal/log"
	"dnsmasqledger/internal/model"
)

func OrderEvents(events []model.ReplayEvent) []model.ReplayEvent {
	out := make([]model.ReplayEvent, len(events))
	copy(out, events)
	sort.Slice(out, func(i, j int) bool {
		if out[i].Seq == out[j].Seq {
			return out[i].Tie < out[j].Tie
		}
		return out[i].Seq < out[j].Seq
	})
	return out
}

func Run(logPath string) (*model.Catalog, int, error) {
	events, err := log.LoadReplay(logPath)
	if err != nil {
		return nil, 0, err
	}
	cat := model.NewCatalog()
	cat.LogPath = logPath

	snap, _ := checkpoint.Load(logPath)
	if snap != nil {
		checkpoint.RestoreCatalog(cat, snap)
	}

	ordered := OrderEvents(events)
	skipThrough := 0
	if snap != nil {
		skipThrough = snap.ThroughSeq
	}

	applied := 0
	ackReplay := make(map[int]bool)

	for _, ev := range ordered {
		if ev.Seq < skipThrough {
			continue
		}
		lease.ExpireDue(cat)
		ok := applyEvent(cat, ev, ackReplay, logPath)
		if ev.Op == "replay_checkpoint" {
			_ = checkpoint.Persist(cat, logPath, ev.ThroughSeq)
			cat.Checkpoint = ev.ThroughSeq
		}
		journal.Append(cat, ev, ok)
		cat.Timeline = append(cat.Timeline, model.TimelineEntry{
			Seq: ev.Seq,
			Op:  ev.Op,
			OK:  ok,
			At:  cat.NowSec,
		})
		applied++
	}
	lease.ExpireDue(cat)
	return cat, applied, nil
}

func applyEvent(cat *model.Catalog, ev model.ReplayEvent, ackReplay map[int]bool, logPath string) bool {
	_ = logPath
	switch ev.Op {
	case "tick":
		cat.NowSec += ev.ElapsedSec
		lease.ExpireDue(cat)
		return true
	case "dhcp_discover":
		return lease.Discover(cat, ev)
	case "dhcp_offer":
		return lease.Offer(cat, ev)
	case "dhcp_request":
		return true
	case "dhcp_ack":
		replay := ackReplay[ev.Seq]
		if !replay {
			ackReplay[ev.Seq] = true
		}
		return lease.Ack(cat, ev, replay)
	case "dhcp_renew":
		return lease.Renew(cat, ev)
	case "dhcp_decline":
		return lease.Decline(cat, ev)
	case "dhcp_release":
		return lease.Release(cat, ev)
	case "replay_checkpoint":
		return true
	default:
		return true
	}
}
