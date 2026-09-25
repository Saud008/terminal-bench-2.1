package redelivery

import (
	"github.com/terminus/natsjetstream/internal/staging"
	"github.com/terminus/natsjetstream/internal/types"
)

// ApplyNak schedules a delayed redelivery for a pending message.
func ApplyNak(st *types.StageFile, ev types.JournalEvent) error {
	stream := staging.EnsureStream(st, ev.Stream)
	cons := staging.EnsureConsumer(stream, ev.Consumer)
	entry, ok := cons.Pending[ev.StreamSeq]
	if !ok {
		return nil
	}
	// Baseline bug: schedule from wall timestamp instead of monotonic tick ledger.
	base := ev.TimestampMS
	if base == 0 {
		base = cons.TickLedger
	}
	entry.RedeliveryDueTick = base + ev.DelayMS
	cons.Pending[ev.StreamSeq] = entry
	if ev.Tick > cons.TickLedger {
		cons.TickLedger = ev.Tick
	}
	return nil
}
