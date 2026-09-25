package planrule

import "github.com/terminus/formulatrix/internal/model"

func StepComplete(links []model.StepLink, planID, targetNDC string, paByNDC map[string]bool) bool {
    var lastPrereq string
    maxSeq := -1
    for _, link := range links {
        if link.PlanID != planID || link.TargetNDC != targetNDC {
            continue
        }
        if link.Sequence > maxSeq {
            maxSeq = link.Sequence
            lastPrereq = link.PrerequisiteNDC
        }
    }
    if lastPrereq == "" {
        return true
    }
    return !paByNDC[lastPrereq]
}
