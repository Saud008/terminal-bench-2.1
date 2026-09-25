package heartbeat

import "github.com/terminus/temporal-signal-replay/internal/model"

// RecordBeat stores heartbeat offset relative to server time base.
func RecordBeat(snap *model.Snapshot, beat model.ActivityBeat) {
	snap.HeartbeatOffset = append(snap.HeartbeatOffset, beat.WorkerTimeMs)
}
