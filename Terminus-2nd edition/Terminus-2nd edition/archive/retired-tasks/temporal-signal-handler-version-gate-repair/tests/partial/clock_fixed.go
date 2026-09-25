package heartbeat

import "github.com/terminus/temporal-signal-replay/internal/model"

func RecordBeat(snap *model.Snapshot, beat model.ActivityBeat) {
	snap.HeartbeatOffset = append(snap.HeartbeatOffset, beat.HeartbeatServerMs)
}
