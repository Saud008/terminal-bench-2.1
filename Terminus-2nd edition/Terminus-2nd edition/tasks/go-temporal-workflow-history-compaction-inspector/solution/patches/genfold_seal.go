package genfold

import "github.com/terminus/wfhistctl/internal/model"

func CountCAN(events []model.HistoryEvent) int {
    n := 0
    for _, ev := range events {
        if ev.Kind == "WorkflowExecutionContinuedAsNew" {
            n++
        }
    }
    return n
}

func Analyze(events []model.HistoryEvent, scenario string) model.CompactionAudit {
    var findings []model.Finding
    for _, ev := range events {
        if ev.Kind == "ActivityTaskScheduled" && ev.Attempt < 0 {
            findings = append(findings, model.Finding{
                Code:       "ATTEMPT_RANGE",
                WorkflowID: ev.WorkflowID,
                Detail:     "negative attempt",
            })
        }
    }
    return model.CompactionAudit{
        Scenario:      scenario,
        FindingCount:  len(findings),
        CanBoundaries: CountCAN(events),
        Findings:      findings,
    }
}

func BumpSeal(cur model.CompactionSeal, canCount int) model.CompactionSeal {
    cur.CompactionSeal = 1 + canCount
    return cur
}
