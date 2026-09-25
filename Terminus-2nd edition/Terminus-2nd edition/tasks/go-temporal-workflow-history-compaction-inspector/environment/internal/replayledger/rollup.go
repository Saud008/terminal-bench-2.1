package replayledger

import (
    "sort"

    "github.com/terminus/wfhistctl/internal/firegate"
    "github.com/terminus/wfhistctl/internal/model"
    "github.com/terminus/wfhistctl/internal/retryledger"
)

func BuildInspectionSnapshot(events []model.HistoryEvent) ([]model.ActivityRow, []model.RiskRow) {
    rows, maxByGen := retryledger.ProjectActivityRows(events)
    pending := firegate.PendingAfterHistory(events)
    wf := ""
    if len(events) > 0 {
        wf = events[len(events)-1].WorkflowID
    }

    riskByGen := map[int]*model.RiskRow{}
    for gen, maxAtt := range maxByGen {
        rr := &model.RiskRow{WorkflowID: wf, RunGeneration: gen, MaxAttempt: maxAtt}
        if maxAtt > 1 {
            rr.RiskCode = "RETRY_CHAIN"
        } else if pending > 0 {
            rr.RiskCode = "TIMER_PENDING"
        } else {
            rr.RiskCode = "CLEAN"
        }
        rr.PendingTimers = pending
        riskByGen[gen] = rr
    }

    var risks []model.RiskRow
    for _, rr := range riskByGen {
        risks = append(risks, *rr)
    }
    sort.Slice(risks, func(i, j int) bool {
        return risks[i].RunGeneration < risks[j].RunGeneration
    })
    sort.Slice(rows, func(i, j int) bool {
        if rows[i].RunGeneration != rows[j].RunGeneration {
            return rows[i].RunGeneration < rows[j].RunGeneration
        }
        if rows[i].ActivityID != rows[j].ActivityID {
            return rows[i].ActivityID < rows[j].ActivityID
        }
        return rows[i].Attempt < rows[j].Attempt
    })
    return rows, risks
}
