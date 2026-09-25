package join

import "github.com/terminus/feast-pit-join/internal/model"

func SelectPIT(events []model.MaterializedEvent, keys []string, entityID, deviceID, sessionID, feature, source string, asOf int64) *model.MaterializedEvent {
	var best *model.MaterializedEvent
	for i := range events {
		ev := &events[i]
		if ev.Feature != feature || ev.Source != source {
			continue
		}
		if !entityMatch(keys, ev, entityID, deviceID, sessionID) {
			continue
		}
		if ev.EventTS >= asOf {
			continue
		}
		if best == nil || ev.EventTS > best.EventTS {
			best = ev
		}
	}
	return best
}

func entityMatch(keys []string, ev *model.MaterializedEvent, entityID, deviceID, sessionID string) bool {
	if len(keys) == 0 {
		return false
	}
	if ev.EntityID != entityID {
		return false
	}
	if len(keys) == 1 {
		return true
	}
	if len(keys) >= 2 {
		second := keys[1]
		if second == "device_id" {
			return true
		}
		if second == "session_id" {
			return ev.SessionID == sessionID
		}
	}
	return false
}
