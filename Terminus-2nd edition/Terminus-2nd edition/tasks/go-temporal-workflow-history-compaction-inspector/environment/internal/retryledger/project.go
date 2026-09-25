package retryledger

import "github.com/terminus/wfhistctl/internal/model"

type activityKey struct {
    gen     int
    actID   string
    attempt int
}

func ProjectActivityRows(events []model.HistoryEvent) ([]model.ActivityRow, map[int]int) {
    tracker := NewTracker()
    status := map[activityKey]string{}
    maxByGen := map[int]int{}

    for _, ev := range events {
        switch ev.Kind {
        case "WorkflowExecutionContinuedAsNew":
            tracker.OnContinuedAsNew()
        case "ActivityTaskScheduled":
            att := tracker.OnScheduled(ev.ActivityID, ev.Attempt)
            status[activityKey{ev.RunGeneration, ev.ActivityID, att}] = "scheduled"
        case "ActivityTaskCompleted":
            status[activityKey{ev.RunGeneration, ev.ActivityID, ev.Attempt}] = "completed"
        case "ActivityTaskFailed":
            status[activityKey{ev.RunGeneration, ev.ActivityID, ev.Attempt}] = "failed"
        }
    }

    var rows []model.ActivityRow
    for key, st := range status {
        score := key.attempt * 10
        if st == "failed" {
            score += 5
        }
        rows = append(rows, model.ActivityRow{
            RunGeneration: key.gen,
            ActivityID:    key.actID,
            Attempt:       key.attempt,
            Status:        st,
            RiskScore:     score,
        })
        if key.attempt > maxByGen[key.gen] {
            maxByGen[key.gen] = key.attempt
        }
    }
    return rows, maxByGen
}
