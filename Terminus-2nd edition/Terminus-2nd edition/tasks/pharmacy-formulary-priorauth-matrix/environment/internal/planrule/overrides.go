package planrule

import "github.com/terminus/formulatrix/internal/model"

func SelectOverride(rules []model.Override, planID, ndc, asOf string) (model.Override, bool) {
    var best model.Override
    found := false
    for _, r := range rules {
        if r.PlanID != planID || r.NDC != ndc {
            continue
        }
        if !DateActive(r.EffectiveStart, r.EffectiveEnd, asOf) {
            continue
        }
        if !found || r.Priority < best.Priority {
            best = r
            found = true
        }
    }
    return best, found
}
