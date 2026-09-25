package replay

import (
	"fmt"
	"sort"

	"github.com/terminus/natsjetstream/internal/ack"
	"github.com/terminus/natsjetstream/internal/filter"
	"github.com/terminus/natsjetstream/internal/redelivery"
	"github.com/terminus/natsjetstream/internal/staging"
	"github.com/terminus/natsjetstream/internal/types"
)

// Apply replays journal events into stage state.
func Apply(events []types.JournalEvent, st *types.StageFile) error {
	sort.SliceStable(events, func(i, j int) bool { return events[i].Seq < events[j].Seq })
	for _, ev := range events {
		switch ev.Op {
		case "PUB":
			if err := applyPub(st, ev); err != nil {
				return err
			}
		case "CONSUMER_UPSERT":
			if err := applyConsumerUpsert(st, ev); err != nil {
				return err
			}
		case "DELIVER":
			if err := applyDeliver(st, ev); err != nil {
				return err
			}
		case "ACK":
			if err := ack.ApplyAck(st, ev); err != nil {
				return err
			}
		case "NAK":
			if err := redelivery.ApplyNak(st, ev); err != nil {
				return err
			}
		case "TERM":
			if err := applyTerm(st, ev); err != nil {
				return err
			}
		default:
			return fmt.Errorf("unknown op %q at seq %d", ev.Op, ev.Seq)
		}
		st.LastAppliedSeq = ev.Seq
	}
	return nil
}

func applyPub(st *types.StageFile, ev types.JournalEvent) error {
	stream := staging.EnsureStream(st, ev.Stream)
	stream.Messages = append(stream.Messages, types.StreamMessage{
		StreamSeq: ev.StreamSeq,
		Subject:   ev.Subject,
	})
	if ev.StreamSeq > stream.MaxSeq {
		stream.MaxSeq = ev.StreamSeq
	}
	return nil
}

func applyConsumerUpsert(st *types.StageFile, ev types.JournalEvent) error {
	stream := staging.EnsureStream(st, ev.Stream)
	cons := staging.EnsureConsumer(stream, ev.Consumer)
	cons.FilterSubject = ev.FilterSubject
	cons.MaxDeliver = ev.MaxDeliver
	cons.RequireAckSync = ev.RequireAckSync
	return nil
}

func applyDeliver(st *types.StageFile, ev types.JournalEvent) error {
	stream := staging.EnsureStream(st, ev.Stream)
	cons := staging.EnsureConsumer(stream, ev.Consumer)
	msg := findMessage(stream, ev.StreamSeq)
	if msg == nil {
		return fmt.Errorf("deliver unknown stream_seq %d at seq %d", ev.StreamSeq, ev.Seq)
	}
	if !filter.MatchFilter(msg.Subject, cons.FilterSubject) {
		return nil
	}
	cons.Pending[ev.StreamSeq] = types.PendingEntry{
		StreamSeq:   ev.StreamSeq,
		DeliveryNum: ev.DeliveryNum,
	}
	if ev.Tick > cons.TickLedger {
		cons.TickLedger = ev.Tick
	}
	return nil
}

func applyTerm(st *types.StageFile, ev types.JournalEvent) error {
	stream := staging.EnsureStream(st, ev.Stream)
	cons := staging.EnsureConsumer(stream, ev.Consumer)
	entry, ok := cons.Pending[ev.StreamSeq]
	if !ok {
		return nil
	}
	if cons.MaxDeliver > 0 && entry.DeliveryNum >= cons.MaxDeliver {
		delete(cons.Pending, ev.StreamSeq)
	}
	if ev.Tick > cons.TickLedger {
		cons.TickLedger = ev.Tick
	}
	return nil
}

func findMessage(stream *types.StreamState, seq uint64) *types.StreamMessage {
	for i := range stream.Messages {
		if stream.Messages[i].StreamSeq == seq {
			return &stream.Messages[i]
		}
	}
	return nil
}
