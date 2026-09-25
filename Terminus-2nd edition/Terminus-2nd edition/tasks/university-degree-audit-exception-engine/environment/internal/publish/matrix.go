package publish

import (
    "encoding/json"
    "os"
    "sort"

    "github.com/terminus/degaudit/internal/model"
)

const (
    logPath    = "/app/work/requirement-eval.json"
    passPath   = "/app/state/evaluation-pass.json"
    reportPath = "/app/output/degree-audit-report.json"
)

type passCounter struct {
    AuditPass int `json:"audit_pass"`
}

type reqRow struct {
    ReqID            string  `json:"req_id"`
    SatisfiedCredits float64 `json:"satisfied_credits"`
    RequiredCredits  float64 `json:"required_credits"`
    Satisfied        bool    `json:"satisfied"`
}

func WriteReport(scenario string) error {
    var counter passCounter
    raw, err := os.ReadFile(passPath)
    if err != nil {
        return err
    }
    if err := json.Unmarshal(raw, &counter); err != nil {
        return err
    }
    if counter.AuditPass <= 0 {
        return os.ErrInvalid
    }
    logRaw, err := os.ReadFile(logPath)
    if err != nil {
        return err
    }
    var logBody struct {
        Scenario  string `json:"scenario"`
        Students  []struct {
            StudentID    string           `json:"student_id"`
            Requirements []model.ReqStatus `json:"requirements"`
        } `json:"students"`
        RunStamp string `json:"run_stamp"`
    }
    if err := json.Unmarshal(logRaw, &logBody); err != nil {
        return err
    }
    var published []map[string]any
    for _, st := range logBody.Students {
        rows := make([]reqRow, 0, len(st.Requirements))
        for _, r := range st.Requirements {
            rows = append(rows, reqRow{
                ReqID:            r.ReqID,
                SatisfiedCredits: r.SatisfiedCredits,
                RequiredCredits:  r.RequiredCredits,
                Satisfied:        r.Satisfied,
            })
        }
        sort.Slice(rows, func(i, j int) bool {
            return rows[i].ReqID > rows[j].ReqID
        })
        published = append(published, map[string]any{
            "student_id":   st.StudentID,
            "requirements": rows,
        })
    }
    if err := os.MkdirAll("/app/output", 0o755); err != nil {
        return err
    }
    body, err := json.Marshal(map[string]any{
        "scenario":  scenario,
        "engine":    "degaudit",
        "run_stamp": logBody.RunStamp,
        "students":  published,
    })
    if err != nil {
        return err
    }
    return os.WriteFile(reportPath, body, 0o644)
}
