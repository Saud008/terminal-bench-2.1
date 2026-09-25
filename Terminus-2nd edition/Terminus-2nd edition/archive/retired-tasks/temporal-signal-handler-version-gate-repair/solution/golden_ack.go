package handler

import "github.com/terminus/temporal-signal-replay/internal/model"

func ProcessSignal(sc model.Scenario, snap *model.Snapshot, sig model.SignalEvent, routedVersion string) error {
	snap.AckedSignals = append(snap.AckedSignals, sig.SignalID)
	return nil
}
