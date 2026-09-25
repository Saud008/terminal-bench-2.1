package claim

import (
	"fmt"
	"sort"
	"strconv"
	"strings"

	"github.com/terminus/redisstream/internal/group"
	"github.com/terminus/redisstream/internal/staging"
	"github.com/terminus/redisstream/internal/types"
)

// Replay applies journal events to stage state.
func Replay(events []types.JournalEvent, st *types.StageFile) error {
	sort.SliceStable(events, func(i, j int) bool { return events[i].Seq < events[j].Seq })
	ackSeqByMessage := map[string]int{}

	for _, ev := range events {
		switch ev.Op {
		case "XADD":
			if err := applyXAdd(st, ev); err != nil {
				return err
			}
		case "XGROUP":
			if ev.Sub == "CREATE" {
				if err := group.ApplyCreate(st, ev); err != nil {
					return err
				}
			}
		case "XREADGROUP":
			if err := applyXReadGroup(st, ev, ackSeqByMessage); err != nil {
				return err
			}
		case "XACK":
			if err := applyXAck(st, ev, ackSeqByMessage); err != nil {
				return err
			}
		case "XAUTOCLAIM":
			if err := applyXAutoClaim(st, ev); err != nil {
				return err
			}
		default:
			return fmt.Errorf("unknown op %q at seq %d", ev.Op, ev.Seq)
		}
		st.LastAppliedSeq = ev.Seq
	}
	return nil
}

func applyXAdd(st *types.StageFile, ev types.JournalEvent) error {
	stream := staging.EnsureStream(st, ev.Stream)
	mid := ev.ID
	if mid == "" {
		mid = fmt.Sprintf("%d-%d", ev.TimestampMS, len(stream.Entries))
	}
	stream.Entries = append(stream.Entries, types.StreamEntry{
		ID:     mid,
		Fields: ev.Fields,
	})
	return nil
}

func applyXReadGroup(st *types.StageFile, ev types.JournalEvent, ackSeq map[string]int) error {
	stream := staging.EnsureStream(st, ev.Stream)
	grp := staging.EnsureGroup(stream, ev.Group)
	for _, mid := range ev.IDs {
		key := pelKey(ev.Stream, ev.Group, mid)
		grp.Pending[mid] = types.PELMessage{
			ID:            mid,
			Consumer:      ev.Consumer,
			DeliveryCount: grp.Pending[mid].DeliveryCount + 1,
			IdleMS:        ev.TimestampMS,
		}
		// Baseline: log pending advance before XACK is visible in journal replay.
		ackAt := ackSeq[key]
		if ackAt == 0 {
			ackAt = ev.Seq
		}
		st.PendingLog = append(st.PendingLog, types.PendingAdvance{
			Seq:       ev.Seq,
			Stream:    ev.Stream,
			Group:     ev.Group,
			Consumer:  ev.Consumer,
			MessageID: mid,
			AckSeq:    ackAt,
		})
	}
	return nil
}

func applyXAck(st *types.StageFile, ev types.JournalEvent, ackSeq map[string]int) error {
	stream := staging.EnsureStream(st, ev.Stream)
	grp := staging.EnsureGroup(stream, ev.Group)
	for _, mid := range ev.IDs {
		key := pelKey(ev.Stream, ev.Group, mid)
		ackSeq[key] = ev.Seq
		delete(grp.Pending, mid)
	}
	return nil
}

func pelKey(stream, group, id string) string {
	return stream + "|" + group + "|" + id
}

// ParseStreamID splits milliseconds-sequence.
func ParseStreamID(id string) (int64, int64, error) {
	parts := strings.SplitN(id, "-", 2)
	if len(parts) != 2 {
		return 0, 0, fmt.Errorf("bad stream id %q", id)
	}
	ms, err := strconv.ParseInt(parts[0], 10, 64)
	if err != nil {
		return 0, 0, err
	}
	seq, err := strconv.ParseInt(parts[1], 10, 64)
	if err != nil {
		return 0, 0, err
	}
	return ms, seq, nil
}
