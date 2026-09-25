package join

import "github.com/terminus/feast-pit-join/internal/model"

func SelectPIT(events []model.MaterializedEvent, keys []string, entityID, deviceID, sessionID, feature, source string, asOf int64) *model.MaterializedEvent {
	var best *model.MaterializedEvent
	for i := range events {
		ev := &events[i]
		if ev.Feature != feature || ev.Source != source {
			continue
		}
		if !EntityMatch(keys, ev, entityID, deviceID, sessionID) {
			continue
		}
		if ev.EventTS > asOf {
			continue
		}
		if best == nil || ev.EventTS > best.EventTS {
			best = ev
		}
	}
	return best
}

func EntityMatch(keys []string, ev *model.MaterializedEvent, entityID, deviceID, sessionID string) bool {
	if len(keys) == 0 || ev.EntityID != entityID {
		return false
	}
	if len(keys) == 1 {
		return true
	}
	switch keys[1] {
	case "device_id":
		return ev.DeviceID == deviceID
	case "session_id":
		return ev.SessionID == sessionID
	default:
		return false
	}
}
