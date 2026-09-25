package ack

import (
	"github.com/terminus/natsjetstream/internal/staging"
	"github.com/terminus/natsjetstream/internal/types"
)

// ApplyAck processes an ACK journal line against consumer pending state.
func ApplyAck(st *types.StageFile, ev types.JournalEvent) error {
	stream := staging.EnsureStream(st, ev.Stream)
	cons := staging.EnsureConsumer(stream, ev.Consumer)

	if _, ok := cons.Pending[ev.StreamSeq]; !ok {
		return nil
	}
	if cons.RequireAckSync && !ev.AckSync {
		return nil
	}
	delete(cons.Pending, ev.StreamSeq)
	if ev.AckSync && ev.StreamSeq > cons.HighWaterSeq {
		cons.HighWaterSeq = ev.StreamSeq
	}
	if ev.Tick > cons.TickLedger {
		cons.TickLedger = ev.Tick
	}
	return nil
}
