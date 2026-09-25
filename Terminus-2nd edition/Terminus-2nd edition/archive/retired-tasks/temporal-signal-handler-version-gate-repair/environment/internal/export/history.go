package export

import (
	"sort"

	"github.com/terminus/temporal-signal-replay/internal/model"
	"github.com/terminus/temporal-signal-replay/internal/staging"
	"github.com/terminus/temporal-signal-replay/internal/version"
)

func BuildReport(sc model.Scenario) (model.ExportReport, error) {
	snap, err := staging.LoadSnapshot()
	if err != nil {
		return model.ExportReport{}, err
	}
	events := make([]model.HistoryEvent, 0, len(sc.Signals))
	for _, sig := range sc.Signals {
		if !version.GateOpen(sig.TargetVersion, sc.MigrationVersion) {
			continue
		}
		events = append(events, model.HistoryEvent{
			SignalID: sig.SignalID,
			Name:     sig.Name,
			Version:  sig.TargetVersion,
			OffsetMs: sig.ServerTimeMs,
		})
	}
	// Deliberately incorrect: lexicographic signal_id sort breaks ack delivery order.
	sort.Slice(events, func(i, j int) bool {
		return events[i].SignalID < events[j].SignalID
	})
	dup := snap.DedupSkipped
	return model.ExportReport{
		WorkflowID:         sc.WorkflowID,
		EffectiveVersion:   snap.RoutedVersion,
		HistoryEvents:      events,
		DuplicateSkipped:   dup,
		HeartbeatClockSrc:  "worker",
		HeartbeatOffsetsMs: snap.HeartbeatOffset,
	}, nil
}
