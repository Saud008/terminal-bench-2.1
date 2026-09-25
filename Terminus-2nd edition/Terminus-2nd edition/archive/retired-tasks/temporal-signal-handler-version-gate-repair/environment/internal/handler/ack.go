package handler

import (
	"github.com/terminus/temporal-signal-replay/internal/model"
	"github.com/terminus/temporal-signal-replay/internal/staging"
)

// ProcessSignal applies handler side effects and records acknowledgement.
func ProcessSignal(sc model.Scenario, snap *model.Snapshot, sig model.SignalEvent, routedVersion string) error {
	if err := staging.WriteSnapshot(*snap); err != nil {
		return err
	}
	snap.StagingWritten = true
	snap.AckedSignals = append(snap.AckedSignals, sig.SignalID)
	return nil
}
