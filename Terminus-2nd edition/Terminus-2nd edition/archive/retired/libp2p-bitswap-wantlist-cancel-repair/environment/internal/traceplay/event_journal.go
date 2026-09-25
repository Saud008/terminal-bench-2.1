package traceplay

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"bswapd/internal/chunkbuf"
	"bswapd/internal/cid"
	"bswapd/internal/creditline"
	"bswapd/internal/model"
	"bswapd/internal/schedhead"
	"bswapd/internal/session"
	"bswapd/internal/peerwant"
)

func LoadEvents(path string) ([]model.Event, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var events []model.Event
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := sc.Text()
		if line == "" || line[0] == '#' {
			continue
		}
		var ev model.Event
		if err := json.Unmarshal([]byte(line), &ev); err != nil {
			return nil, err
		}
		events = append(events, ev)
	}
	if err := sc.Err(); err != nil {
		return nil, err
	}
	sort.Slice(events, func(i, j int) bool { return events[i].Seq < events[j].Seq })
	return events, nil
}

func ReplayFile(path, sessionName string) (*model.Session, error) {
	events, err := LoadEvents(path)
	if err != nil {
		return nil, err
	}
	sess := session.New(sessionName)
	for _, ev := range events {
		if err := applyEvent(sess, ev); err != nil {
			return nil, fmt.Errorf("seq %d: %w", ev.Seq, err)
		}
	}
	return sess, nil
}

func applyEvent(sess *model.Session, ev model.Event) error {
	switch ev.Op {
	case "want":
		canon, err := cid.CanonicalKey(ev.CID)
		if err != nil {
			return err
		}
		sess.Wants[ev.CID] = &model.WantEntry{DisplayCID: ev.CID, Priority: ev.Priority, Canonical: canon}
		session.Touch(sess)
	case "merge_wants":
		peerwant.MergePeerWants(sess, ev.Wants)
		session.Touch(sess)
	case "cancel":
		peerwant.ApplyCancel(sess, ev.CID)
		session.Touch(sess)
	case "block_start":
		canon, err := cid.CanonicalKey(ev.CID)
		if err != nil {
			return err
		}
		chunkbuf.StartBlock(sess, canon, ev.Peer, ev.Seq)
		creditline.CreditDelivery(sess, ev.Peer, ev.CID, ev.Bytes)
		session.Touch(sess)
	case "block_part":
		canon, err := cid.CanonicalKey(ev.CID)
		if err != nil {
			return err
		}
		chunkbuf.PartialChunk(sess, canon, ev.Peer, ev.Bytes)
		session.Touch(sess)
	case "block_done":
		canon, err := cid.CanonicalKey(ev.CID)
		if err != nil {
			return err
		}
		chunkbuf.CompleteBlock(sess, canon, ev.Peer, ev.Bytes)
		creditline.CreditDelivery(sess, ev.Peer, ev.CID, ev.Bytes)
		ent, ok := sess.Wants[ev.CID]
		pri := 0
		if ok {
			pri = ent.Priority
			delete(sess.Wants, ev.CID)
		}
		sess.Delivered = append(sess.Delivered, model.Delivery{
			CID: ev.CID, Peer: ev.Peer, Bytes: ev.Bytes, Priority: pri,
		})
		session.Touch(sess)
	case "tick":
		session.ApplyIdleTick(sess, ev.IdleMS)
	default:
		return fmt.Errorf("unknown op %q", ev.Op)
	}
	return nil
}

func MetricsHead(sess *model.Session) (string, int, bool) {
	return schedhead.HeadAfterCancelMerge(sess)
}
