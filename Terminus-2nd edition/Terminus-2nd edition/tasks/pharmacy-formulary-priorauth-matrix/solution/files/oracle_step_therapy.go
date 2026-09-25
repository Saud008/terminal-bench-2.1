package planrule

import (
    "sort"

    "github.com/terminus/formulatrix/internal/model"
    "github.com/terminus/formulatrix/internal/formndc"
)

func StepComplete(links []model.StepLink, planID, targetNDC string, paByNDC map[string]bool) bool {
    var chain []model.StepLink
    for _, link := range links {
        if link.PlanID == planID && link.TargetNDC == targetNDC {
            chain = append(chain, link)
        }
    }
    if len(chain) == 0 {
        return true
    }
    sort.Slice(chain, func(i, j int) bool { return chain[i].Sequence < chain[j].Sequence })
    for _, link := range chain {
        prereq := formndc.NormalizeNDC(link.PrerequisiteNDC)
        if paByNDC[prereq] {
            return false
        }
    }
    return true
}
