package firegate

import "github.com/terminus/wfhistctl/internal/model"

func PendingAfterHistory(events []model.HistoryEvent) int {
    lane := NewLane()
    for _, ev := range events {
        switch ev.Kind {
        case "TimerStarted":
            lane.Start(ev.TimerID, ev.TimestampMs)
        case "TimerCanceled":
            lane.Cancel(ev.TimerID)
        case "TimerFired":
            lane.Fire(ev.TimerID, ev.TimestampMs)
        }
    }
    return lane.PendingCount()
}
