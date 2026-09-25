package reqclose

import "github.com/terminus/degaudit/internal/model"

func EvaluateRequirements(
    reqs []model.Requirement,
    reqCourses []model.RequirementCourse,
    folded map[string]float64,
    waived map[string]bool,
    activeSub map[string]string,
) []model.ReqStatus {
    direct := map[string]float64{}
    for _, rc := range reqCourses {
        effective := rc.ReqID
        if sub, ok := activeSub[rc.ReqID]; ok {
            effective = sub
        }
        if credits, ok := folded[rc.CourseCode]; ok {
            direct[effective] += credits
        }
    }
    children := map[string][]string{}
    parentOf := map[string]string{}
    for _, r := range reqs {
        if r.ParentReqID != "" {
            children[r.ParentReqID] = append(children[r.ParentReqID], r.ReqID)
            parentOf[r.ReqID] = r.ParentReqID
        }
    }
    status := map[string]model.ReqStatus{}
    for _, r := range reqs {
        sat := direct[r.ReqID]
        if waived[r.ReqID] {
            sat = r.RequiredCredits
        }
        status[r.ReqID] = model.ReqStatus{
            ReqID:            r.ReqID,
            SatisfiedCredits: sat,
            RequiredCredits:  r.RequiredCredits,
            Satisfied:        sat >= r.RequiredCredits,
        }
    }
    for _, r := range reqs {
        if r.ParentReqID != "" {
            continue
        }
        var walk func(string)
        walk = func(id string) {
            for _, child := range children[id] {
                walk(child)
                childSt := status[child]
                if childSt.Satisfied {
                    parent := status[id]
                    parent.SatisfiedCredits += childSt.SatisfiedCredits
                    parent.Satisfied = parent.SatisfiedCredits >= parent.RequiredCredits
                    status[id] = parent
                }
            }
        }
        walk(r.ReqID)
    }
    out := make([]model.ReqStatus, 0, len(reqs))
    for _, r := range reqs {
        out = append(out, status[r.ReqID])
    }
    return out
}
