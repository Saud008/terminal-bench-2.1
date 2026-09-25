package audit

import (
    "encoding/json"
    "os"

    "github.com/terminus/degaudit/internal/cataloggate"
    "github.com/terminus/degaudit/internal/dbread"
    "github.com/terminus/degaudit/internal/idemstamp"
    "github.com/terminus/degaudit/internal/model"
    "github.com/terminus/degaudit/internal/repeatfold"
    "github.com/terminus/degaudit/internal/reqclose"
    "github.com/terminus/degaudit/internal/substgate"
    "github.com/terminus/degaudit/internal/transmap"
)

const (
    logPath     = "/app/work/requirement-eval.json"
    passPath    = "/app/state/evaluation-pass.json"
    materialPath = "/app/state/transcript-material.json"
)

type passCounter struct {
    AuditPass int    `json:"audit_pass"`
    RunStamp  string `json:"run_stamp"`
}

func Run(scenario string) error {
    db, err := dbread.Open("/app/state/registrar-workspace.db")
    if err != nil {
        return err
    }
    defer db.Close()
    meta, err := dbread.ReadMeta(db)
    if err != nil {
        return err
    }
    if v := os.Getenv("TB3_AUDIT_DATE"); v != "" {
        meta.AuditDate = v
    }
    courses, err := dbread.ReadCourses(db)
    if err != nil {
        return err
    }
    courseMap := map[string]model.Course{}
    for _, c := range courses {
        courseMap[c.CourseCode] = c
    }
    catalogYear := cataloggate.EffectiveCatalogYear(meta, courses)
    filtered := map[string]model.Course{}
    for code, c := range courseMap {
        if cataloggate.CourseAllowed(c, catalogYear) {
            filtered[code] = c
        }
    }
    equivs, err := dbread.ReadTransferEquiv(db)
    if err != nil {
        return err
    }
    subs, err := dbread.ReadSubstitutions(db)
    if err != nil {
        return err
    }
    activeSub := substgate.ActiveSubstitutions(meta.AuditTerm, subs)
    reqs, err := dbread.ReadRequirements(db)
    if err != nil {
        return err
    }
    reqCourses, err := dbread.ReadRequirementCourses(db)
    if err != nil {
        return err
    }
    students, err := dbread.ReadStudents(db)
    if err != nil {
        return err
    }
    materialRaw, err := os.ReadFile(materialPath)
    if err != nil {
        return err
    }
    var materialDoc map[string]any
    if err := json.Unmarshal(materialRaw, &materialDoc); err != nil {
        return err
    }
    digest, _ := materialDoc["material_fingerprint"].(string)
    stamp := idemstamp.RunStamp(scenario, digest)
    var studentReports []map[string]any
    for _, sid := range students {
        enrolls, err := dbread.ReadEnrollments(db, sid)
        if err != nil {
            return err
        }
        mapped := make([]model.Enrollment, 0, len(enrolls))
        for _, e := range enrolls {
            code := e.CourseCode
            if e.IsTransfer {
                code = transmap.MapTransfer(code, catalogYear, equivs)
            }
            e.CourseCode = code
            if _, ok := filtered[code]; !ok {
                continue
            }
            mapped = append(mapped, e)
        }
        foldedList := repeatfold.FoldEnrollments(mapped, filtered)
        foldedCredits := map[string]float64{}
        for _, fc := range foldedList {
            foldedCredits[fc.CourseCode] = fc.Credits
        }
        waivers, err := dbread.ReadWaivers(db, sid)
        if err != nil {
            return err
        }
        waived := map[string]bool{}
        for _, w := range waivers {
            waived[w.ReqID] = true
        }
        statuses := reqclose.EvaluateRequirements(reqs, reqCourses, foldedCredits, waived, activeSub)
        studentReports = append(studentReports, map[string]any{
            "student_id":   sid,
            "requirements": statuses,
        })
    }
    if err := os.MkdirAll("/app/work", 0o755); err != nil {
        return err
    }
    logBody, err := json.Marshal(map[string]any{
        "scenario":  scenario,
        "students":  studentReports,
        "run_stamp": stamp,
    })
    if err != nil {
        return err
    }
    if err := os.WriteFile(logPath, logBody, 0o644); err != nil {
        return err
    }
    var counter passCounter
    if raw, err := os.ReadFile(passPath); err == nil {
        _ = json.Unmarshal(raw, &counter)
    }
    counter.AuditPass++
    counter.RunStamp = stamp
    passRaw, err := json.Marshal(counter)
    if err != nil {
        return err
    }
    return os.WriteFile(passPath, passRaw, 0o644)
}
