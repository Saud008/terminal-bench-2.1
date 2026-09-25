package export

import (
	"github.com/terminus/temporal-signal-replay/internal/model"
	"github.com/terminus/temporal-signal-replay/internal/staging"
)

func BuildReport(sc model.Scenario) (model.ExportReport, error) {
	snap, err := staging.LoadSnapshot()
	if err != nil {
		return model.ExportReport{}, err
	}
	byID := make(map[string]model.SignalEvent, len(sc.Signals))
	for _, sig := range sc.Signals {
		if _, ok := byID[sig.SignalID]; !ok {
			byID[sig.SignalID] = sig
		}
	}
	events := make([]model.HistoryEvent, 0, len(snap.AckedSignals))
	for _, sid := range snap.AckedSignals {
		sig, ok := byID[sid]
		if !ok {
			continue
		}
		events = append(events, model.HistoryEvent{
			SignalID: sid,
			Name:     sig.Name,
			Version:  sig.TargetVersion,
			OffsetMs: sig.ServerTimeMs,
		})
	}
	return model.ExportReport{
		WorkflowID:         sc.WorkflowID,
		EffectiveVersion:   snap.RoutedVersion,
		HistoryEvents:      events,
		DuplicateSkipped:   snap.DedupSkipped,
		HeartbeatClockSrc:  "server",
		HeartbeatOffsetsMs: snap.HeartbeatOffset,
	}, nil
}
